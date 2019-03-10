function postScores(url, data, redirect){
	return $.ajax(url, {
		method: "POST",
		data: JSON.stringify(data),
		contentType: "application/json",
		error: () => flash("post failas", "error"),
		success: () => {
			window.location.href = redirect;
		}
	});
}

export function flash(mes, type){
	// TODO
	alert(mes);
}

export function trigger(target, event, detail){
	// Tää ei välttämättä toimi safarissa XXX
	const evt = new CustomEvent(event, {
		detail,
		bubbles: true
	});
	target.dispatchEvent(evt);
}

export function submit(root, opt){
	const $elem = $(root);
	// TODO animoi tässä postissa tää submit buttoni
	// ja olis kiva jos se postin jälkeen flashais jotakin
	const post = data => postScores(opt.postUrl, data, opt.returnUrl);
	$elem.on("click", () => {
		trigger($elem[0], "judging:submit", { post });
	});
}

export function setError($input, opt){
	opt = opt||{};
	const clazz = opt.errorClass || "j-error";
	const event = opt.event || "click";

	$input.addClass(clazz).one(event, () => $input.removeClass(clazz));
}

export class Judging {

	constructor($elem, opt){
		this.$elem = $elem;
		const $submit = opt.submit ? $(opt.submit) : $elem.parent();
		$submit.on("judging:submit", evt => {
			this.onSubmit(evt.detail.post);
		});

		this.init(opt);
	}

	init(opt){

	}

	trigger(event, detail){
		// Safarissa (eli kaikissa iOS selaimissa) ei toimi EventTarget
		// joten eventit pitää laittaa dom elementtiin :(
		trigger(this.$elem[0], event, detail);
	}

	getState(){
		return {};
	}

	verifySubmit(){
		return true;
	}

	onSubmit(submit){
		const state = this.getState();
		if(this.verifySubmit(state)){
			submit(state);
		}
	}

}
