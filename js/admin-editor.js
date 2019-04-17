/*
export const renderLoader = (text="") =>
	`<td colspan=10 class='a-editor-loader'>
		<i class='fas fa-spinner'></i>
		${text}
	</td>`;
*/

export const esc = str => str.replace('"', '&quot;');

export class EditorComponent extends EventTarget {

	constructor($root){
		super();
		this.$root = $root;
		this.init();
	}

	init(){
		this.$table = $("<table class='a-editor-table'></table>");
		this.$thead = $("<thead></thead>").appendTo(this.$table);
		this.$tbody = $("<tbody></tbody>").appendTo(this.$table);
		this.$root.html(this.$table);

		this.$thead.append(this.renderHeader());

		this.initNew();
		this.initControls();
	}

	initNew(){
		$(`<tr class='a-editor-new'>
			<td colspan=10><i class='fas fa-plus-circle'></i> Luo uusi</td>
		</tr>`)
			.appendTo(this.$thead)
			.on("click", () => this.dispatchCreate());
	}

	initControls(){
		// XXX: Tässä appendTo() ja detach() siksi että jquery tekee tälle dom noden
		// ja listenerit toimii, jos sitä ei ensin appendaa niin on() ei tee mitään...

		// Pitäskö tähän laittaa joku mahollisuus pistää aliluokista omia nappeja

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
			.on("click", () => this.dispatchSubmit());

		$(`<button type='button' class='action-button a-editor-cancel' style='margin-left:20px'>
				<i class='fas fa-ban'></i> Peruuta
			</button>`)
			.appendTo($container)
			.on("click", () => this.cancel());
	}

	add(obj){
		this.$tbody.append(this.renderObject(obj));
	}

	update(objid, obj){
		const $target = this.findObject(objid);

		if($target)
			$target.replaceWith(this.renderObject(obj));
		else
			this.add(obj);
	}

	delete(objid){
		this.findObject(objid).remove();
	}

	clear(){
		this.$tbody.html("");
	}

	setObjects(objs){
		this.clear();
		for(let o of objs)
			this.add(o);
	}

	setEdit(objid, opt){
		this.cancel();

		const $editor = this.createEditor(opt);

		if(objid){
			const $target = this.findObject(objid);
			$target.replaceWith($editor);
			this.$editTarget = $target;
		}else{
			this.$tbody.prepend($editor);
		}

		this.$editor = $editor;
		this.showControls($editor);
	}

	/*
	setLoading(objid){
		this.findObject(objid).replaceWith(this.renderLoader(objid));
	}
	*/

	showControls($target){
		$target.after(this.$editControls.detach());
	}

	hideControls(){
		this.$editControls.detach();
	}

	dispatchCreate(){
		this.dispatchEvent(new CustomEvent("create"));
	}

	dispatchSubmit(){
		const detail = this.onSubmit();
		this.dispatchEvent(new CustomEvent("submit", { detail }));
	}

	dispatchEdit(obj){
		this.dispatchEvent(new CustomEvent("edit", { detail: obj }));
	}

	dispatchDelete(obj){
		this.dispatchEvent(new CustomEvent("delete", { detail: obj }));
	}

	cancel(){
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


	// --- Override nämä ---

	findObject(objid){
		return null;
	}

	onSubmit(){
		return {};
	}

	renderHeader(){
		return "";
	}

	renderObject(obj){
		return "";
	}

	createEditor(opt){
		return "";
	}

	/*
	renderLoader(objid){
		return `<tr>${renderLoader()}</tr>`;
	}
	*/

}

// XXX: Tää ei oikeen kuulu tänne tälle pitäs varmaan keksii parempi paikka
export async function tryAwait(x){
	try {
		return await x;
	} catch(e) {
		console.error(e);
		notify(e, {type: "error"});
		throw e;
	}
}
