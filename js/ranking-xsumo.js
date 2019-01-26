const makeMatrixEvent = (ev, s1, s2) => //`${s1.score_value} - ${s2.score_value}`;
	`<span class='r-xsumo-matrix-event-s1'>${s1.score_value}</span> - 
		<span class='r-xsumo-matrix-event-s2'>${s2.score_value}</span>`;

const syncScroll = ($e1, $e2, axis="xy") => {
	$e1.on("scroll", () => {
		if(axis.includes("y"))
			$e2.scrollTop($e1.scrollTop());
		if(axis.includes("x"))
			$e2.scrollLeft($e1.scrollLeft());
	});
};

class XSumoMatrix {

	constructor($elem, teams, events){
		this.$elem = $elem;
		this.teams = teams;
		this.events = events;
		this.init();
	}

	init(){
		console.log("init xsumomatrix, teams:", this.teams, "events:", this.events);
		this.$elem.addClass("r-xsumo-matrix");

		const $top = $("<div class='r-xsumo-matrix-top'></div>");
		$top.append("<div class='r-xsumo-matrix-colfirst'></div>");
		const $colheader = $("<div class='r-xsumo-matrix-colheader'></div>").appendTo($top);
		for(let t of this.teams)
			$colheader.append(`<div class='r-xsumo-matrix-colname'><div>${t.name}</div></div>`);
		// XXX: tää antaa scrollata "yli" että kierretyt nimet näkyy
		$colheader.append("<div style='width:1000px'>&nbsp;</div>");

		const $bottom = $("<div class='r-xsumo-matrix-bottom'></div>");
		const $rowheader = $("<div class='r-xsumo-matrix-rowheader'></div>").appendTo($bottom);
		for(let t of this.teams)
			$rowheader.append(`<div class='r-xsumo-matrix-rowname'>${t.name}</div>`);

		const $grid = $("<div class='r-xsumo-matrix-grid'></div>").appendTo($bottom);
		this.$table = $("<table class='r-xsumo-matrix-table'></table>").appendTo($grid);
		for(let es of this.events){
			const $tr = $("<tr></tr>").appendTo(this.$table);
			for(let e of es){
				if(e){
					$tr.append(`<td>${makeMatrixEvent(e.event, e.score1, e.score2)}</td>`);
				}else{
					$tr.append("<td class='r-xsumo-matrix-skip'></td>");
				}
			}
			// XXX: tää on siks että headeri näkyy kokonaan
			$tr.append("<th style='width:100px'></th>");
			// XXX: tää siks että toimii vaikka containeri on isompi ku table
			$tr.append("<th style='width:100%'></th>");
		}

		//$bottom.append("<div style='width:100px'></div>");

		this.$elem.append($top, $bottom);
		syncScroll($grid, $colheader, "x");
		syncScroll($grid, $rowheader, "y");
	}

}

export function xsumoMatrix(root, teams, events){
	return new XSumoMatrix($(root), teams, events);
}
