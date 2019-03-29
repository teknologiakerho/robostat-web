let getContainer = () => {
	const $root = document.createElement("div");
	$root.className = "notify-container";
	$root.style.position = "fixed";
	$root.style.bottom = 0;
	$root.style.right = 0;
	document.body.appendChild($root);

	getContainer = () => $root;
	return $root;
};

class Notification {

	constructor($root){
		this.$root = $root;
		this.init();
	}

	init(){
		this.$root.addEventListener("click", () => this.close());
	}

	timeout(ms){
		if(this._timeout)
			clearTimeout(this._timeout);

		this._timeout = setTimeout(() => this.close(), ms);
	}

	close(){
		if(this._timeout){
			clearTimeout(this._timeout);
			delete this._timeout;
		}

		this.$root.classList.remove("notify-appear-js");

		// reflow koska ainakaan chrome ei muuten toista animaatiota
		void this.$root.offsetHeight;

		this.$root.classList.add("notify-disappear-js");
		this.$root.addEventListener("animationend", () => this.$root.remove());
	}

}

export default function notify(mes, opt){
	opt = Object.assign({
		type: "info",
		"class": ""
	}, opt);

	const $root = document.createElement("div");
	$root.className = `notify notify-js notify-appear-js notify-${opt.type} ${opt["class"]}`;
	$root.innerHTML = mes;
	getContainer().appendChild($root);

	const notification = new Notification($root);

	if(opt.timeout)
		notification.timeout(opt.timeout);
}
