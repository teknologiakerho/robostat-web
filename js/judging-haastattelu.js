import {Judging} from "./judging-common.js";

class Haastattelu extends Judging {

	getState(){
		const $checkbox = this.$elem.find("[data-haast-check]");
		return { done: $checkbox.is(":checked") };
	}

}

export function haastattelu(root){
	return new Haastattelu($(root), {});
}
