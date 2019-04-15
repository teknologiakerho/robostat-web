import {ApiClient} from "./api-client.js";

const formatTimestamp = ts => moment(ts, "X").format("D.M.YYYY H:mm");
const parseTimestamp = ts => moment(ts, "D.M.YYYY H:mm").unix();

const renderId = id => `<span class='a-editor-id'>${id}</span>`;

class BlockEditorView {

	constructor($root){
		this.$root = $root;
		this.init();
	}

	init(){
		this.$table = $("<table class='a-editor-table'></table>");
		this.$thead = $(this.renderHeader()).appendTo(this.$table);
		this.$tbody = $("<tbody></tbody>").appendTo(this.$table);
		this.$root.html(this.$table);

		this.$table.on("mouseenter mouseleave", ".a-editable", e => {
			const type = e.target.getAttribute("data-type");
			const value = e.target.getAttribute("data-value");
			this.highlight(type, value, e.type === "mouseenter");
		});

		this.$table.on("click", ".a-editor-new", () => this.$root.trigger("editor:create-event"));

		this.initControls();
		this.initContextMenu();
	}

	initControls(){
		// XXX: Tässä appendTo() ja detach() siksi että jquery tekee tälle dom noden
		// ja listenerit toimii, jos sitä ei ensin appendaa niin on() ei tee mitään...
		this.$editControls = $("<tr class='a-editor-active a-editor-controls'></tr>")
			.appendTo(this.$tbody)
			.detach();

		const $cell = $("<td colspan=10></td>")
			.appendTo(this.$editControls);

		const $container = $("<div class='a-editor-controls-container'></div>")
			.appendTo($cell);
		
		$(`<button type='button' class='action-button a-editor-submit'>
				<i class='fas fa-check'></i> Tallenna
			</button>`)
			.appendTo($container)
			.on("click", () => this.submit());

		$(`<button type='button' class='action-button a-editor-cancel'>
				<i class='fas fa-ban'></i> Peruuta
			</button>`)
			.appendTo($container)
			.on("click", () => this.cancelEdit());
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
				callback: (_, opt) => {
					this.$root.trigger("editor:edit-event", {
						id: opt.$trigger.closest("[data-event-id]").attr("data-event-id")
					});
				}
			},

			/*
			"sep1": "---",

			"replace-all": {
				name: "Korvaa kaikki",
				icon: "fas fa-exchange-alt",
				callback: (_, opt) => {

				}
			},

			"delete-all": {
				name: "Poista kaikki",
				icon: "fas fa-minus-square",
				callback: (_, opt) => {

				}
			},

			"sep2": "---",
			*/

			"delete-event": {
				name: "Poista",
				icon: "fas fa-trash-alt",
				callback: (_, opt) => {
					this.$root.trigger("editor:delete-event", {
						id: opt.$trigger.closest("[data-event-id]").attr("data-event-id")
					});
				}
			}
		};

		contextMenu({
			selector: ".a-editable[data-type='judge']",
			items: {
				"judge": {
					name: "Siirry tuomarointiin",
					icon: "fas fa-angle-double-right",
					callback: (_, opt) => {
						this.$root.trigger("editor:judge-event", {
							id: opt.$trigger.closest("[data-event-id]").attr("data-event-id"),
							as: opt.$trigger.closest("[data-type='judge']").attr("data-value")
						});
					}
				},
				"s": "---",
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

	setEdit(event, opt){
		this.cancelEdit();

		const $editor = $(this.renderEditor(event, opt));

		console.log(opt);

		$editor.find("[data-field='arena']").selectize({
			items: [event.arena],
			options: opt.arenas,
			create: true,
			maxItems: 1,
		});

		$editor.find("[data-field='teams']").selectize({
			options: opt.teams,
			items: event.teams.map(t => t.id),
			valueField: "id",
			labelField: "name",
			searchField: "name"
		});

		$editor.find("[data-field='judges']").selectize({
			options: opt.judges,
			items: event.judges.map(j => j.id),
			valueField: "id",
			labelField: "name",
			searchField: "name"
		});

		if(event.id){
			const $target = this.$table.find(`[data-event-id="${event.id}"]`);
			$target.replaceWith($editor);
			this.$editTarget = $target;
		}else{
			this.$tbody.prepend($editor);
		}

		this.$editor = $editor;
		this.showControls($editor);
	}

	submit(){
		const id = this.$editor.attr("data-event-id");
		const ts_sched = parseTimestamp(this.$editor.find("[data-field='ts']").val());
		const arena = this.$editor.find("[data-field='arena']").val();
		const teams = this.$editor.find("[data-field='teams']").val();
		const judges = this.$editor.find("[data-field='judges']").val();

		this.$root.trigger("editor:submit-event", {
			id, ts_sched, arena, teams, judges
		});
	}

	cancelEdit(){
		if(this.$editor){
			if(this.$editTarget)
				this.$editor.replaceWith(this.$editTarget);
			else
				this.$editor.remove();

			delete this.$editTarget;
			delete this.$editor;
		}

		this.hideControls();
	}

	showControls($target){
		$target.after(this.$editControls.detach());
	}

	hideControls(){
		this.$editControls.detach();
	}

	setEvents(events){
		this.$tbody.html("");
		for(let e of events)
			this.addEvent(e);
	}

	addEvent(e){
		this.$tbody.append(this.renderEvent(e));
	}

	setLoading(id){
		const $target = this.$tbody.find(`[data-event-id=${id}]`);
		$target.replaceWith(this.renderLoader(id));
	}

	updateEvent(e){
		const $target = this.$tbody.find(`[data-event-id=${e.id}]`);
		if(!$target)
			this.addEvent(e);
		else
			$target.replaceWith(this.renderEvent(e));
	}

	deleteEvent(id){
		this.$tbody.find(`[data-event-id=${id}]`).remove();
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

	renderHeader(){
		return (
			`<thead>
				<tr class='a-editor-header'>
					<th><i class='fas fa-clock'></i> Aika</th>
					<th><i class='fas fa-map-marker'></i> Kenttä</th>
					<th><i class='fas fa-users'></i> Osallistujat</th>
					<th><i class='fas fa-user-tie'></i> Tuomarit</th>
				</tr>
				<tr class='a-editor-new'>
					<td colspan=10><i class='fas fa-plus-circle'></i> Luo uusi</td>
				</tr>
			</thead>`
		);
	}

	renderEvent(e){
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

	renderEditor(e, opt){
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

	renderLoader(id){
		return (
			`<tr class='a-editor-loading' data-event-id=${id}>
				<td colspan=10>
					<i class='fas fa-spinner a-editor-loader-icon'></i>
				</td>
			</tr>`
		);
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

}

class BlockEditor {

	constructor(view, block, client, scoringEndpoint){
		this.view = view;
		this.block = block;
		this.client = client;
		this.scoringEndpoint = scoringEndpoint;
		this.events = {};

		this.init();
		this.loadEvents().then(() => this.loadScores());
	}

	init(){
		this.view.$root.on("editor:create-event", () => {
			this.createEvent();
		});

		this.view.$root.on("editor:edit-event", (e, detail) => {
			this.editEvent(detail.id);
		});

		this.view.$root.on("editor:submit-event", (e, detail) => {
			const {id, ...data} = detail;
			this.view.hideControls();

			if(id)
				this.updateEvents({[id]: data});
			else
				this.updateNewEvent(data);
		});

		this.view.$root.on("editor:delete-event", (e, detail) => {
			this.deleteEvent(detail.id);
		});

		if(this.scoringEndpoint){
			this.view.$root.on("editor:judge-event", (e, detail) => {
				const url = `${this.scoringEndpoint}/${detail.id}?as=${detail.as}`;
				window.open(url, "_blank");
			});
		}
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

		this.view.setEdit({
			ts_sched: defaultTs,
			arena: defaultArena,
			teams: [],
			judges: []
		}, autocomplete);
	}

	async editEvent(id){
		id = +id;
		const event = this.events[id];
		const autocomplete = await this.getAutocomplete();
		this.view.setEdit(event, autocomplete);
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
		const events = await this._request("/events", {
			b: this.block,
			sort: "ts"
		});

		this.events = {};
		for(let e of events)
			this.events[e.id] = e;

		this.view.setEvents(events);
	}

	async loadScores(ids){
		const scores = await this._request("/scores",
			ids ? { e: ids } : { b: this.block }
		);

		for(let eid of Object.keys(scores)){
			this.view.setScores(eid, scores[eid]);
		}
	}

	async updateEvents(evs){
		for(let id of Object.keys(evs))
			this.view.setLoading(id);

		const updateData = await this._post("/events/update", evs);
		await this._loadTeams();
		await this._loadJudges();

		for(let id of Object.keys(updateData)){
			updateData[id].id = id;
			const ev = this._makeEvent(updateData[id]);
			this.events[id] = ev;
			this.view.updateEvent(ev);
		}

		await this.loadScores(Object.keys(updateData));

		notify(`${Object.keys(updateData).length} Suoritusta päivitetty`, {
			type: "success",
			timeout: 5000
		});
	}

	async updateNewEvent(data){
		this.view.cancelEdit();

		const eventData = await this._post("/events/create", {
			...data,
			block_id: this.block
		});
		await this._loadTeams();
		await this._loadJudges();

		const event = this._makeEvent(eventData);
		this.events[event.id] = event;
		this.view.addEvent(event);

		await this.loadScores([event.id]);

		notify("Suoritus lisätty", {
			type: "success",
			timeout: 5000
		});
	}

	async deleteEvent(id){
		this.view.setLoading(id);

		await this._tryRequest(this.client.request(`/events/${id}/delete`, "", {
			method: "POST"
		}));

		delete this.events[id];
		this.view.deleteEvent(id);

		notify("Suoritus poistettu", {
			type: "success",
			timeout: 5000
		});
	}

	async _request(path, params){
		return await this._tryRequest(this.client.request(path, params));
	}

	async _post(path, json, params){
		return await this._tryRequest(this.client.postJson(path, params, json));
	}

	async _tryRequest(req){
		try {
			return await req;
		} catch(e) {
			console.error(e);
			notify(e, {type: "error"});
			throw e;
		}
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
			const teams = await this._request("/teams");
			for(let t of teams)
				this._teams[t.id] = t;
		}

		return this._teams;
	}

	async _loadJudges(){
		if(!this._judges){
			this._judges = {};
			const judges = await this._request("/judges");
			for(let j of judges)
				this._judges[j.id] = j;
		}

		return this._judges;
	}

}

export function blockEditor(root, opt){
	const view = new BlockEditorView($(root));
	const client = new ApiClient(opt.api);
	const editor = new BlockEditor(view, opt.block, client, opt.scoringEndpoint);
	return editor;
}
