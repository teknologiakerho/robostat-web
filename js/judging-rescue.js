import {Judging, setError} from "./judging-common.js";

const getWeight = el => +el.getAttribute("data-res-weight");

const getExplanation = scores =>
	scores.filter(([weight, value]) => value > 0)
		.map(([weight, value]) => `${weight} × ${value}`)
		.join(" + ");

const getSection = $elem => $elem.closest("[data-res-section]").attr("data-res-section");

const getRadioMap = $radios => {
	const ret = {};

	$radios.each((_, el) => {
		ret[el.name] = {
			value: el.value,
			score: +el.getAttribute("data-res-weight")
		};
	});

	return ret;
};

const getScoreboxMap = scoreboxes => {
	const ret = {};

	for(let s of scoreboxes){
		if(!ret[s.name]){
			ret[s.name] = {
				values: [],
				score: 0
			};
		}

		ret[s.name].values.push({
			value: s.value,
			count: s.score,
			weight: s.weight
		});

		ret[s.name].score += s.score * s.weight;
	}

	return ret;
};

const getScore = state => {
	let ret = 0;

	for(let k of Object.keys(state))
		ret += state[k].score;

	return ret;
};

class Rescue extends Judging {

	init(opt){
		this.initRadios();
		this.initScoreboxes();
		this.$timeMin = this.$elem.find("input[name=time_min]");
		this.$timeSec = this.$elem.find("input[name=time_sec]");

		if(opt.eventData)
			this.initEvent(opt.eventData);
	}

	initRadios(){
		this.$radios = this.$elem.find("input[type=radio][data-res-weight]");

		this.$radios.on("change", e => {
			const section = getSection($(e.target));
			if(section)
				this.updateSection(section);
			this.update();
		});
	}

	initScoreboxes(){
		this.scoreboxes = this.$elem.find("[data-res-scorebox]")
			.toArray()
			.map(el => new Scorebox($(el)));

		this.$elem.on("res.scorebox:change", (e, {source}) => {
			if(source.section)
				this.updateSection(source.section);
			this.update();
		});
	}

	initEvent(eventData){
		console.log("init", eventData);

		let updateSections = {};

		this.$radios.each((_, el) => {
			if(eventData[el.name]){
				updateSections[getSection($(el))] = 1;
				el.checked = eventData[el.name] === el.value;
			}
		});

		this.scoreboxes.forEach(s => {
			if(eventData[s.name]){
				updateSections[s.section] = 1;
				s.setScore(eventData[s.name][s.value]);
			}
		});

		if(eventData.time){
			this.$timeMin.val(eventData.time/60|0);
			this.$timeSec.val(eventData.time%60);
		}

		for(let k of Object.keys(updateSections))
			this.updateSection(k);
		this.update();
	}

	verifySubmit(){
		const time = this.getTime();

		if(time.min === 0 && time.sec === 0){
			setError(this.$timeMin);
			setError(this.$timeSec);
			return false;
		}

		if(isNaN(time.min) || time.min < 0){
			setError(this.$timeMin);
			return false;
		}

		if(isNaN(time.sec) || time.sec < 0 || time.sec > 60){
			setError(this.$timeSec);
			return false;
		}

		return true;
	}

	getState(section=null){
		let $radios = this.$radios.filter(":checked");
		let scoreboxes = this.scoreboxes;

		if(section){
			$radios = $radios.filter((_, el) => getSection($(el)) === section);
			scoreboxes = scoreboxes.filter(s => s.section === section);
		}

		const ret = {
			scores: {
				...getRadioMap($radios),
				...getScoreboxMap(scoreboxes)
			}
		};

		if(!section)
			ret.time = this.getTime();

		return ret;
	}

	getTime(){
		return {
			min: +this.$timeMin.val(),
			sec: +this.$timeSec.val()
		};
	}

	updateSection(section){
		const $update = this.$elem.find(`[data-res-total=${section}]`);

		if($update.length > 0){
			const state = this.getState(section);
			$update.html(`${getScore(state.scores)}`);
		}
	}

	update(){
		const state = this.getState();
		const score = getScore(state.scores);
		this.$elem.find("[data-res-total=total]").html(`${score}`);

		this.trigger("res:update", { state, score });
	}

}

class Scorebox {

	constructor($elem){
		this.$elem = $elem;
		this.$inner = $("<span class='j-res-scorebox-inner'></span>");
		this.$elem.html(this.$inner);
		this.name = $elem.attr("data-res-scorebox");
		this.value = $elem.attr("data-res-value");
		this.weight = +$elem.attr("data-res-weight");
		this.$elem.addClass("j-res-scorebox");
		this.$elem.addClass(`j-res-scorebox-${this.value}`);
		this.section = getSection($elem);
		this.score = 0;

		this.setupListeners();
		this.update();
	}

	setupListeners(){
		let timeout;
		let c = 0;

		this.$elem.on("mousedown touchstart", e => {
			if(timeout)
				return;

			if(e.button === 2){
				this.add(-1);
				return;
			}

			timeout = setTimeout(() => {
				this.add(-1);
				timeout = undefined;
			}, 1000);
		}).on("mouseleave touchleave", () => {
			clearTimeout(timeout);
			timeout = undefined;
		}).on("click", e => {
			if(timeout){
				clearTimeout(timeout);
				timeout = undefined;
				this.add(1);
			}
		}).on("contextmenu", false);
	}

	add(num){
		if(!this.setScore(this.score + num))
			return false;

		this.animate(num > 0 ? this.value : "remove");
		this.$elem.trigger("res.scorebox:change", { source: this });
	}

	animate(style){
		const animClass = `j-res-scorebox-${style}-flash`;

		// if the animation didn't end yet remove the class anyway
		this.$elem.removeClass(animClass);
		// reflow
		void this.$elem[0].offsetHeight;

		this.$elem.addClass(animClass)
			.one("animationend", () => this.$elem.removeClass(animClass));
	}

	setScore(newScore){
		if(newScore < 0)
			newScore = 0;

		if(newScore != this.score){
			this.score = newScore;
			this.update();
			return true;
		}

		return false;
	}

	update(){
		this.$inner.toggleClass("j-res-scorebox-inactive", this.score === 0);
		this.$inner.html(`${this.score} × ${this.weight}`);
	}

}

export function rescue(root, opt){
	return new Rescue($(root), opt||{});
}
