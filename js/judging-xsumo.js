import {Judging, setError} from "./judging-common.js";

const makeRound = (content) => 
	`<div class='j-xsumo-round'>
		<div class='j-xsumo-round-header'>
			<button class='plain-input j-xsumo-round-close' type='button'>
				Poista
			</button>
			<span class='j-xsumo-round-title'></span>
		</div>
		${content}
	</div>`;

const makeInput = ({name, type, value, text, clazz}) =>
	`<div class='j-xsumo-input-container'>
		<input class='j-xsumo-input plain-input ${clazz}' type='${type}' name='${name}'
			value='${value}' />
		<span class='j-xsumo-input-text'>${text}</span>
	</div>`;

const uncheckOthers = ($parent, target) => {
	const name = target.getAttribute("name");
	$parent.find(`input[name='${name}']`)
		.filter((_, el) => el != target)
		.prop("checked", false);
};

const calcBasicScores = rounds => {
	const ret = [0, 0];

	for(let r of rounds){
		if(r.first !== undefined)
			ret[r.first]++;

		if(r.result === "tie"){
			ret[0]++;
			ret[1]++;
		}else if(r.result !== undefined){
			ret[r.result] += 3;
		}
	}

	return ret;
};

class XSumo extends Judging {

	init(opt){
		this.teams = opt.teams;
		this.allowEmptyFirst = opt.allowEmptyFirst;
		this.rounds = [];

		this.initUI();

		if(opt.rounds)
			this.initRounds(opt.rounds);
		else
			this.addRound();

		this.update();
	}

	initUI(){
		this.$elem.addClass("j-xsumo");

		this.$teamLabels = [
			$("<div class='j-xsumo-p1'></div>").appendTo(this.$elem),
			$("<div class='j-xsumo-p2'></div>").appendTo(this.$elem)
		];

		this.$roundsContainer = $("<div class='j-xsumo-rounds'></div>").appendTo(this.$elem);
		
		$(`<button class='plain-input j-xsumo-round-add'><span>+</span></button>`)
			.appendTo(this.$elem)
			.on("click", () => this.addRound() && this.update() && false);
	}

	initRounds(rounds){
		// implement subclass
	}

	createRound(){
		// implement subclass
	}

	addRound(){
		const round = this.createRound();
		round.setNumber(this.rounds.length);
		this.rounds.push(round);
		this.trigger("xsumo:addround");
		return round;
	}

	removeRound(round){
		round.$elem.remove();
		let idx = this.rounds.indexOf(round);
		this.rounds.splice(idx, 1);

		for(;idx<this.rounds.length;idx++)
			this.rounds[idx].setNumber(idx);

		this.trigger("xsumo:removeround");
		this.update();
	}

	verifySubmit(){
		return this.rounds.reduce((ret, round) => round.verify() && ret, true);
	}

	getState(){
		return {
			team1: this.teams[0].id,
			team2: this.teams[1].id,
			rounds: this.rounds.map(r => r.getState())
		};
	}

	update(){
		const state = this.getState();
		const [s1, s2] = calcBasicScores(state.rounds);
		this.trigger("xsumo:update", {
			state,
			score1: s1,
			score2: s2
		});

		this.showScore(s1, s2);
	}

	showScore(s1, s2){
		this.$teamLabels[0].html(`${this.teams[0].name} - <strong>${s1}</strong>`);
		this.$teamLabels[1].html(`<strong>${s2}</strong> - ${this.teams[1].name}`);
	}

}

class XSumoRound {

	constructor($elem, parent){
		this.$elem = $elem;
		this.parent = parent;

		this.init();
	}

	init(){
		this.$elem.find("button").on("click", () => {
			if(confirm("Haluatko varmasti poistaa erän?")){
				this.remove();
			}
		});
	}

	verify(){
		return true;
	}

	setNumber(num){
		this.$elem.find(".j-xsumo-round-title").text(`Erä ${num+1}`);
	}

	remove(){
		this.parent.removeRound(this);
	}

	getState(){
		// implement subclass
		return {}
	}

}

class XSumoBasic extends XSumo {

	initRounds(rounds){
		for(let r of rounds){
			const round = this.addRound();
			round.setFirst(r.first);
			round.setResult(r.result);
		}
	}

	createRound(){
		const check = (name, value, text, clazz) => makeInput({
			name, value, text, clazz,
			type: "checkbox"
		});

		// Tässä ei saa olla whitespacea inputtien välissä
		const $el = $(makeRound(
			check("first", 0, "Ensimmäinen", "j-xsumo-left")
			+ "<div class='j-xsumo-input-container'>"
				+ "<input name='first' class='j-xsumo-input plain-input' type='checkbox' disabled />"
				+ "</div>"
			+ check("first", 1, "Ensimmäinen", "j-xsumo-right")
			+ check("result", 0, "Voitto", "j-xsumo-left")
			+ check("result", "tie", "Tasapeli", "j-xsumo-mid")
			+ check("result", 1, "Voitto", "j-xsumo-right")
			+"</div>"
		)).appendTo(this.$roundsContainer);

		return new XSumoBasicRound($el, this);
	}

}

class XSumoBasicRound extends XSumoRound {

	init(){
		super.init();

		this.$elem.on("change", "input[type=checkbox]", e => {
			const target = e.currentTarget;

			if(target.checked)
				uncheckOthers(this.$elem, target);

			this.parent.update();
		});
	}

	setNumber(num){
		super.setNumber(num);
		this.$elem.find("input[name^=first]").prop("name", `first.${num}`);
		this.$elem.find("input[name^=result]").prop("name", `result.${num}`);
	}

	setFirst(first){
		if(first == null)
			this.$elem.find("input[name^=first]").prop("checked", false);
		else
			// event handler will uncheck other boxes
			this.$elem.find(`input[name^=first][value=${first}]`).prop("checked", true);
	}

	setResult(result){
		if(result == null)
			this.$elem.find("input[name^=result]").prop("checked", false);
		else
			this.$elem.find(`input[name^=result][value=${result}]`).prop("checked", true);
	}

	getFirst(){
		// 0, 1: winner
		// undefined: both lose
		return this.$elem.find("input[name^=first]:checked").val();
	}

	getResult(){
		// 0, 1: winner
		// "tie": tie
		// undefined: both lose
		return this.$elem.find("input[name^=result]:checked").val();
	}

	getState(){
		return {
			first: this.getFirst(),
			result: this.getResult()
		};
	}

	verify(){
		if(!this.parent.allowEmptyFirst && this.getFirst() === undefined){
			setError(this.$elem);
			return false;
		}

		return true;
	}

}

/** TODO FIX */

/*
class XSumoInnokas extends XSumo {

	initRounds(rounds){
		console.warn("XSumoInnokas#initRounds unimplemented");
	}

	createRound(isNew=true){
		const firstCheck = (value, clazz) => makeInput({
			value, clazz,
			name: "first",
			text: "Ensimmäinen",
			type: "checkbox",
			containerClass: "uk-width-1-3"
		});

		const $el = $(makeRound(
			firstCheck(0, "j-xsumo-left")
			+ "<div class='uk-width-1-3 uk-display-inline-block'></div>"
			+ firstCheck(1, "j-xsumo-right")
		)).appendTo(this.$roundsContainer);

		const ret = new XSumoInnokasRound($el, this);

		if(isNew)
			$el.one("change", "input", () => ret.addPseudoRound());

		return ret;
	}

}

class XSumoInnokasRound extends XSumoRound {

	constructor($elem, parent){
		super($elem, parent);
		this.pseudorounds = [];
	}

	init(){
		super.init();

		this.$elem.on("change", "input[type=checkbox]", e => {
			if(e.currentTarget.checked)
				uncheckOthers(this.$elem, e.currentTarget);

			this.parent.updateScore();
		});
	}

	setNumber(num){
		super.setNumber(num);
		this.number = num;
		this.$elem.find("input[name^=first]").prop("name", `first.${num}`);
		for(let i=0;i<this.pseudorounds.length;i++)
			this.pseudorounds[i].setNumber(num, i);
	}

	addPseudoRound(isNew=true){
		const check = (name, value, clazz) => makeInput({
			name, value, clazz,
			text: Math.abs(value),
			type: "checkbox",
			containerClass: "uk-width-1-3"
		});

		const $el = $(
			"<div class='j-xsumo-pseudoround uk-width-1-1 uk-text-large'>"
			+ "<div class='uk-width-2-5'>"
				+ check("result", 3, "j-xsumo-left")
				+ check("result", 2, "j-xsumo-left")
				+ check("result", 1, "j-xsumo-left")
			+ "</div>"
			+ "<div class='uk-width-1-5'></div>"
			+ "<div class='uk-width-2-5'>"
				+ check("result", -1, "j-xsumo-right")
				+ check("result", -2, "j-xsumo-right")
				+ check("result", -3, "j-xsumo-right")
			+ "</div>"
			+"</div>"
		).appendTo(this.$elem);

		if(isNew)
			$el.one("change", "input", () => this.addPseudoRound());

		const ret = new XIPseudoRound($el, this);

		ret.setNumber(this.number, this.pseudorounds.length);
		this.pseudorounds.push(ret);
		return ret;
	}

	removePseudoRound(pr){
		pr.$elem.remove();
		let idx = this.pseudorounds.indexOf(pr);
		this.pseudorounds.splice(idx, 1);

		for(;idx<this.pseudorounds.length;idx++)
			this.pseudorounds[idx].setNumber(this.number, idx);

		this.parent.updateScore();
	}

	getFirst(){
		return this.$elem.find("input[name^=first]:checked").val()
	}

	getScores(){
		const first = this.getFirst();
		const ret = [0, 0];

		if(first !== undefined)
			ret[first]++;

		for(let p of this.pseudorounds){
			const res = p.getResult();
			if(res !== undefined)
				// ret[joukkue] += score
				ret[+(res<0)] += Math.abs(res);
		}

		return ret;
	}

}

class XIPseudoRound {

	constructor($elem, parent){
		this.$elem = $elem;
		this.parent = parent;

		this.init();
	}

	init(){
		this.$elem.on("change", "input", e => {
			if(!e.currentTarget.checked){
				// valinta peruutettiin, joten poistetaan (pseudo)kierros
				this.remove();
			}
		});
	}

	setNumber(r, p){
		this.$elem.find("[name^=result]").prop("name", `result.${r}.${p}`);
	}

	remove(){
		this.parent.removePseudoRound(this);
	}

	getResult(){
		return this.$elem.find("[name^=result]:checked").val()
	}
	
}

export function innokas(root, submit, eventData){
	return new XSumoInnokas($(root), $(submit), eventData);
}

export function master(root, submit, eventData){
	// TODO
	return innokasa(root, submit, eventData);
}
*/

export function xsumoBasic(root, opt){
	return new XSumoBasic($(root), opt);
}
