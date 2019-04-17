import {ApiClient} from "./api-client.js";
import {EditorComponent, esc, tryAwait} from "./admin-editor.js";

const getObjId = $elem => $elem.closest("[data-id]").attr("data-id");

class DbEditorComponent extends EditorComponent {

	init(){
		super.init();

		this.$tbody.on("click", ".a-editor-edit", e => {
			this.dispatchEdit({id: getObjId($(e.target))});
		});

		this.$tbody.on("click", ".a-editor-delete", e => {
			this.dispatchDelete({id: getObjId($(e.target))});
		});
	}

	findObject(id){
		return this.$tbody.find(`[data-id=${id}]`);
	}

	createEditor(obj){
		return $(this.renderEditor(obj));
	}

	renderActions(){
		return (
			`<button type='button' class='plain-input a-editor-action a-editor-edit'>
				<i class='fas fa-edit'></i>
			</button>
			<button type='button' class='plain-input a-editor-action a-editor-delete'>
				<i class='fas fa-trash-alt'></i>
			</button>`
		);
	}

}

class TeamsEditorComponent extends DbEditorComponent {

	onSubmit(){
		const id = this.$editor.attr("data-id");
		const name = this.$editor.find("input[name='name']").val();
		const school = this.$editor.find("input[name='school']").val();
		const shadow = this.$editor.find("input[name='shadow']").is(":checked");
		
		return { id, name, school, shadow };
	}

	renderHeader(){
		return (
			`<tr class='a-editor-header'>
				<th>Id</th>
				<th>Nimi</th>
				<th>Koulu</th>
				<th>Piilota</th>
				<th>Toiminnot</th>
			</tr>`
		);
	}

	renderObject(team){
		return (
			`<tr class='a-editor-row a-editor-db-row' data-id=${team.id}>
				<td class='a-editor-db-id'>${team.id}</td>
				<td class='a-editor-db-name'>${team.name}</td>
				<td class='a-editor-db-school'>${team.school}</td>
				<td class='a-editor-db-shadow'>${team.shadow ? "Kyllä" : "Ei"}</td>
				<td class='a-editor-db-actions'>
					${this.renderActions()}
				</td>
			</tr>`
		);
	}

	renderEditor(team){
		return (
			`<tr class='a-editor-active' ${team.id ? `data-id=${team.id}` : ""}>
				<td class='a-editor-db-id'>${team.id || ""}</td>
				<td class='a-editor-db-name'>
					<input type="text" name="name" value="${esc(team.name)}" />
				</td>
				<td class='a-editor-db-school'>
					<input type="text" name="school" value="${esc(team.school)}" />
				</td>
				<td class='a-editor-db-shadow'>
					<input type="checkbox" name="shadow" ${team.shadow && "checked" || ""}>
				</td>
				<td class='a-editor-db-actions'></td>
			</tr>`
		);
	}

}

class JudgesEditorComponent extends DbEditorComponent {

	onSubmit(){
		const id = this.$editor.attr("data-id");
		const name = this.$editor.find("input[name='name']").val();

		let key = this.$editor.find("input[name='key']").val();
		if(key === "")
			key = null;

		return {id, name, key};
	}

	renderHeader(){
		return (
			`<tr class='a-editor-header'>
				<th>Id</th>
				<th>Nimi</th>
				<th>Avain</th>
				<th>Toiminnot</th>
			</tr>`
		);
	}

	renderObject(judge){
		return (
			`<tr class='a-editor-row a-editor-db-row' data-id=${judge.id}>
				<td class='a-editor-db-id'>${judge.id}</td>
				<td class='a-editor-db-name'>${judge.name}</td>
				${ judge.key ? 
					`<td class='a-editor-db-key'>${("*").repeat(judge.key.length)}</td>` :
					`<td class='a-editor-db-key a-editor-db-key-missing'>Ei asetettu</td>`
				}
				<td class='a-editor-db-actions'>
					${this.renderActions()}
				</td>
			</tr>`
		);
	}

	renderEditor(judge){
		return (
			`<tr class='a-editor-active' ${judge.id ? `data-id=${judge.id}` : ""}>
				<td class='a-editor-db-id'>${judge.id || ""}</td>
				<td class='a-editor-db-name'>
					<input type="text" name="name" value="${esc(judge.name)}" />
				</td>
				<td class='a-editor-db-key'>
					<input type="text" name="key"
						value="${judge.key && esc(judge.key) || ""}" />
				</td>
				<td class='a-editor-db-actions'></td>
			</tr>`
		);
	}

}

class DbEditor {

	constructor(view, client){
		this.view = view;
		this.client = client;
		this.objects = {};

		this.init();
		tryAwait(this.loadObjects());
	}

	init(){
		this.view.addEventListener("create", () => this.create());

		this.view.addEventListener("submit", ({detail}) => {
			tryAwait(this.update(detail)).then(() => this.view.hideControls());
		});

		this.view.addEventListener("edit", ({ detail }) => this.edit(detail.id));
		this.view.addEventListener("delete", ({ detail }) => tryAwait(this.delete(detail.id)));
	}

	async loadObjects(){
		const objs = await this.requestObjects();
		for(let o of objs)
			this.objects[o.id] = o;
		this.view.setObjects(objs);
	}

	create(){
		this.view.setEdit(null, this.createObject());
	}

	async update(data){
		const obj = data.id ? (await this.postUpdate(data)) : (await this.postNew(data));
		this.objects[obj.id] = obj;
		this.view.cancel();

		if(data.id)
			this.view.update(obj.id, obj);
		else
			this.view.add(obj)

		notify("Päivitys onnistui", {
			type: "success",
			timeout: 5000
		});
	}

	edit(id){
		this.view.setEdit(id, this.objects[id]);
	}

	async delete(id){
		await this.postDelete(id);

		delete this.objects[id];
		this.view.delete(id);

		notify("Poisto onnistui", {
			type: "success",
			timeout: 5000
		});
	}

	createObject(){
		return {};
	}

	async requestObjects(){
		return [];
	}

	async postUpdate(data){
		
	}

	async postNew(data){

	}

	async postDelete(id){

	}

}

class TeamsEditor extends DbEditor {

	createObject(){
		return {
			name: "",
			school: "",
			shadow: false
		};
	}

	async requestObjects(){
		return await this.client.request("/teams", {
			include_shadows: true
		});
	}

	async postUpdate(data){
		return await this.client.postJson(`/teams/${data.id}/update`, "", data);
	}

	async postNew(data){
		return await this.client.postJson(`/teams/create`, "", data);
	}

	async postDelete(id){
		return await this.client.request(`/teams/${id}/delete`, "", { method: "POST" });
	}

}

class JudgesEditor extends DbEditor {

	createObject(){
		return {
			name: "",
			key: ""
		};
	}

	async requestObjects(){
		return await this.client.request("/judges", {
			with_keys: true
		});
	}

	async postUpdate(data){
		return await this.client.postJson(`/judges/${data.id}/update`, "", data);
	}

	async postNew(data){
		return await this.client.postJson(`/judges/create`, "", data);
	}

	async postDelete(id){
		return await this.client.request(`/judges/${id}/delete`, "", { method: "POST" });
	}

}

export function teamsEditor(root, opt){
	const view = new TeamsEditorComponent($(root));
	const client = new ApiClient(opt.api);
	return new TeamsEditor(view, client);
}

export function judgesEditor(root, opt){
	const view = new JudgesEditorComponent($(root));
	const client = new ApiClient(opt.api);
	return new JudgesEditor(view, client);
}
