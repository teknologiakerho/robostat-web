import {ApiClient} from "./api-client.js";
import {EditorComponent, tryAwait} from "./admin-editor.js";

const getEnclosingEvent = $elem => $elem.closest("[data-event-id]").attr("data-event-id");

const formatTimestamp = ts => moment(ts, "X").format("D.M.YYYY H:mm");
const parseTimestamp = ts => moment(ts, "D.M.YYYY H:mm").unix();

const renderId = id => `<span class='a-editor-id'>${id}</span>`;

class BlockEditorComponent extends EditorComponent {

	init(){
		super.init();

		this.$table.on("mouseenter mouseleave", ".a-editable", e => {
			const type = e.target.getAttribute("data-type");
			const value = e.target.getAttribute("data-value");
			this.highlight(type, value, e.type === "mouseenter");
		});

		this.initContextMenu();
	}
	
	initContextMenu(){
		const contextMenu = opt => $.contextMenu({
			trigger: "left",
			hideOnSecondTrigger: true,
			appendTo: this.$root[0],
			...opt
		});

		const editItems = {
			"edit-event": {
				name: "Muokkaa",
				icon: "fas fa-edit",
				callback: (_, opt) => this.dispatchEdit({id: getEnclosingEvent(opt.$trigger)})
			},

			"delete-event": {
				name: "Poista",
				icon: "fas fa-trash-alt",
				callback: (_, opt) => this.dispatchDelete({id: getEnclosingEvent(opt.$trigger)})
			}
		};

		contextMenu({
			selector: ".a-editable[data-type='judge']",
			items: {
				"judge": {
					name: "Siirry tuomarointiin",
					icon: "fas fa-angle-double-right",
					callback: (_, opt) => {
						const id = getEnclosingEvent(opt.$trigger);
						const as = opt.$trigger.closest("[data-type='judge']").attr("data-value");
						this.dispatchEvent(new CustomEvent("judge-event", {detail:{ id, as }}));
					}
				},
				"s": "---",
				"reset-judging": {
					name: "Pyyhi tuomarointi",
					icon: "fas fa-history",
					callback: (_, opt) => {
						const id = getEnclosingEvent(opt.$trigger);
						const jid = opt.$trigger.closest("[data-type='judge']").attr("data-value");
						this.dispatchEvent(new CustomEvent("reset-judging", {detail: {id, jid}}));
					}
				},
				"ss": "---",
				...editItems
			}
		});

		contextMenu({
			selector: ".a-editable[data-type='team']",
			items: { ...editItems }
		});

		contextMenu({
			selector: ".a-editable[data-type='arena']",
			items: { ...editItems }
		});

		contextMenu({
			selector: ".a-editable[data-type='ts']",
			items: { ...editItems }
		});
	}

	highlight(type, value, on){
		this.$table
			.find(`.a-editable[data-type="${type}"][data-value="${value}"]`)
			.toggleClass("a-editable-highlight", on);
	}

	findObject(id){
		return this.$tbody.find(`[data-event-id=${id}]`);
	}

	onSubmit(){
		const id = this.$editor.attr("data-event-id");
		const ts_sched = parseTimestamp(this.$editor.find("[data-field='ts']").val());
		const arena = this.$editor.find("[data-field='arena']").val();
		const teams = this.$editor.find("[data-field='teams']").val();
		const judges = this.$editor.find("[data-field='judges']").val();

		return {id, ts_sched, arena, teams, judges};
	}

	renderHeader(){
		return (
			`<tr class='a-editor-header'>
				<th><i class='fas fa-clock'></i> Aika</th>
				<th><i class='fas fa-map-marker'></i> Kenttä</th>
				<th><i class='fas fa-users'></i> Osallistujat</th>
				<th><i class='fas fa-user-tie'></i> Tuomarit</th>
			</tr>`
		);
	}

	renderObject(e){
		return (
			`<tr class='a-editor-row' data-event-id="${e.id}">
				<td class='a-editor-time'>
					<span class='a-editable' data-type="ts" data-value="${e.ts_sched}">
						${formatTimestamp(e.ts_sched)}
					</span>
				</td>
				<td class='a-editor-arena'>
					<span class='a-editable' data-type="arena" data-value="${e.arena}">
						${e.arena}
					</span>
				</td>
				<td class='a-editor-teams'>
					<div class='a-editor-multi-container'>
						${e.teams.map(t =>
							`<span class='a-editor-multi a-editable' data-type="team"
								data-value="${t.id}">
								${t.name} (${renderId(t.id)})
							</span>`).join("")}
					</div>
				</td>
				<td class='a-editor-judges'>
					<div class='a-editor-multi-container'>
						${e.judges.map(j =>`
							<span class='a-editor-multi a-editable' data-type="judge"
								data-value="${j.id}">
								${j.name} (${renderId(j.id)})
								<span class='a-editor-judge-scores'></span>
							</span>`).join("")}
					</div>
				</td>
			</tr>`
		);
	}

	createEditor(opt){
		const event = opt.event;
		const autocomplete = opt.autocomplete;
		const $editor = $(this.renderEditor(event));

		console.log(opt);

		$editor.find("[data-field='arena']").selectize({
			items: [event.arena],
			options: autocomplete.arenas,
			create: true,
			maxItems: 1,
		});

		$editor.find("[data-field='teams']").selectize({
			options: autocomplete.teams,
			items: event.teams.map(t => t.id),
			valueField: "id",
			labelField: "name",
			searchField: "name"
		});

		$editor.find("[data-field='judges']").selectize({
			options: autocomplete.judges,
			items: event.judges.map(j => j.id),
			valueField: "id",
			labelField: "name",
			searchField: "name"
		});

		return $editor;
	}

	renderEditor(e){
		// XXX: tässä date inputissa vois käyttää datetime-local input typeä
		// mutta javascriptissä ei ole mitään strftime/strptimen tapaista
		// joten sen käsittely on liian aivokuollutta.
		
		// XXX: Tässä varmaan olis parempikin tapa tehä tän datetimen tyyli
		// kun laittaa class="selectize-input"

		return (
			`<tr class='a-editor-active' ${e.id ? `data-event-id=${e.id}` : ""}>
				<td class='a-editor-time'>
					<div class='selectize-input'>
						<input type="text" data-field="ts"
							value="${isNaN(e.ts_sched) ? 
								e.ts_sched : 
								formatTimestamp(e.ts_sched)}" />
					</div>
				</td>
				<td class='a-editor-arena'>
					<input type="text" data-field="arena"/>
				</td>
				<td class='a-editor-teams'>
					<select multiple data-field="teams"></select>
				</td>
				<td class='a-editor-judges'>
					<select multiple data-field="judges"></select>
				</td>
			`
		);
	}

	setScores(id, scores){
		const $target = this.$tbody.find(`[data-event-id=${id}]`);
		const judgeScores = {};

		for(let s of scores){
			if(!judgeScores[s.judge_id])
				judgeScores[s.judge_id] = [];
			if(s.score)
				judgeScores[s.judge_id].push(s);
		}

		for(let jid of Object.keys(judgeScores)){
			const scores = judgeScores[jid];
			const $scores = $target.find(`[data-type='judge'][data-value="${jid}"]`)
				.find(".a-editor-judge-scores");

			$scores.html(this.renderScores(scores));
		}
	}

	renderScores(scores){
		if(scores.length === 0){
			return "<i class='fas fa-times a-editor-no-judgings'></i>";
		}

		return (
			`<i class='fas fa-check a-editor-have-judgings'></i> ${
				scores.map(s => `(${renderId(s.team_id)})
					<i class='fas fa-long-arrow-alt-right'></i>
					${s.score.desc}`
				).join(", ")
			}`
		);
	}

	renderLoader(id){
		return (
			`<tr class='a-editor-loading' data-event-id=${id}>
				${renderLoader()}
			</tr>`
		);
	}

}

class BlockEditor {

	constructor(view, opt){
		this.view = view;
		this.block = opt.block;
		this.client = opt.client;
		this.scoringEndpoint = opt.scoringEndpoint;
		this.events = {};

		this.init();
		tryAwait(this.loadEvents().then(() => this.loadScores()));
	}

	init(){
		this.view.addEventListener("create", () => tryAwait(this.createEvent()));

		this.view.addEventListener("submit", ({ detail }) => {
			const {id, ...data} = detail;
			const promise = id ? this.updateEvents({[id]: data}) : this.updateNewEvent(data);
			tryAwait(promise).then(() => this.view.hideControls());
		});

		this.view.addEventListener("edit", ({ detail }) => {
			tryAwait(this.editEvent(detail.id));
		});

		this.view.addEventListener("delete", ({ detail }) => {
			tryAwait(this.deleteEvent(detail.id));
		});

		if(this.scoringEndpoint){
			this.view.addEventListener("judge-event", ({ detail }) => {
				const url = `${this.scoringEndpoint}/${detail.id}?as=${detail.as}`;
				window.open(url, "_blank");
			});
		}

		this.view.addEventListener("reset-judging", ({ detail }) => {
			tryAwait(this.resetJudging(detail.id, detail.jid));
		});
	}

	async createEvent(){
		const autocomplete = await this.getAutocomplete();

		let defaultTs = 0, defaultArena = "";
		const events = Object.values(this.events).sort((a, b) => b.ts_sched - a.ts_sched);

		if(events.length > 0){
			const lastTs = events[0].ts_sched;
			const prev = events.find(e => e.ts_sched < lastTs);
			if(prev)
				defaultTs = lastTs + (lastTs - prev.ts_sched);
			defaultArena = events[0].arena;
		}

		this.view.setEdit(null, {
			event: {
				ts_sched: defaultTs,
				arena: defaultArena,
				teams: [],
				judges: [],
			},
			autocomplete
		});
	}

	async editEvent(id){
		id = +id;
		const event = this.events[id];
		const autocomplete = await this.getAutocomplete();
		this.view.setEdit(id, {event, autocomplete});
	}

	async getAutocomplete(){
		const arenas = {};

		for(let e of Object.values(this.events))
			arenas[e.arena] = 1;

		return {
			arenas: Object.keys(arenas).map(a => ({value: a, text: a})),
			teams: Object.values(await this._loadTeams()),
			judges: Object.values(await this._loadJudges())
		};
	}

	async loadEvents(){
		const events = await this.client.request("/events", {
			b: this.block,
			sort: "ts"
		});

		this.events = {};
		for(let e of events)
			this.events[e.id] = e;

		this.view.setObjects(events);
	}

	async loadScores(ids){
		const scores = await this.client.request("/scores",
			ids ? { e: ids } : { b: this.block }
		);

		for(let eid of Object.keys(scores)){
			this.view.setScores(eid, scores[eid]);
		}
	}

	async updateEvents(evs){
		//for(let id of Object.keys(evs))
		//	this.view.setLoading(id);

		const updateData = await this.client.postJson("/events/update", "", evs);
		await this._loadTeams();
		await this._loadJudges();

		for(let id of Object.keys(updateData)){
			updateData[id].id = id;
			const ev = this._makeEvent(updateData[id]);
			this.events[id] = ev;
			this.view.update(id, ev);
		}

		await this.loadScores(Object.keys(updateData));

		notify(`${Object.keys(updateData).length} Suoritusta päivitetty`, {
			type: "success",
			timeout: 5000
		});
	}

	async updateNewEvent(data){
		this.view.cancel();

		const eventData = await this.client.postJson("/events/create", "", {
			...data,
			block_id: this.block
		});
		await this._loadTeams();
		await this._loadJudges();

		const event = this._makeEvent(eventData);
		this.events[event.id] = event;
		this.view.add(event);

		await this.loadScores([event.id]);

		notify("Suoritus lisätty", {
			type: "success",
			timeout: 5000
		});
	}

	async deleteEvent(id){
		//this.view.setLoading(id);

		await this.client.request(`/events/${id}/delete`, "", {
			method: "POST"
		});

		delete this.events[id];
		this.view.delete(id);

		notify("Suoritus poistettu", {
			type: "success",
			timeout: 5000
		});
	}

	async resetJudging(eventId, judgeId){
		await this.client.request(`/judgings/${eventId}/${judgeId}/reset`, "", {
			method: "POST"
		});

		await this.loadScores([eventId]);

		notify("Tuomarointi pyyhitty", {
			type: "success",
			timeout: 5000
		});
	}

	_makeEvent(data){
		const teams = [];
		for(let tid of data.teams)
			teams.push(this._teams[tid]);

		const judges = [];
		for(let jid of data.judges)
			judges.push(this._judges[jid]);

		return {
			id: data.id,
			arena: data.arena,
			ts_sched: data.ts_sched,
			teams,
			judges
		};
	}

	async _loadTeams(){
		if(!this._teams){
			this._teams = {};
			const teams = await this.client.request("/teams");
			for(let t of teams)
				this._teams[t.id] = t;
		}

		return this._teams;
	}

	async _loadJudges(){
		if(!this._judges){
			this._judges = {};
			const judges = await this.client.request("/judges");
			for(let j of judges)
				this._judges[j.id] = j;
		}

		return this._judges;
	}

}

export function blockEditor(root, opt){
	const view = new BlockEditorComponent($(root));
	const client = new ApiClient(opt.api);

	return new BlockEditor(view, {
		client,
		view,
		block: opt.block,
		scoringEndpoint: opt.scoringEndpoint
	});
}
