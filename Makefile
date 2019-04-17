SASS = sassc
ROLLUP = rollup
BUBLE = buble
UGLIFYJS = terser
NODEMON = nodemon

#SASS_ARGS = -t compact
SASS_ARGS = -t compressed
ROLLUP_ARGS =
BUBLE_ARGS = -y dangerousForOf --objectAssign Object.assign
UGLIFYJS_ARGS = -c -m

STATIC = robostat/web/static
#DIST = $(STATIC)/dist
DIST = $(STATIC)

JS = $(addprefix $(DIST)/, judging.min.js ranking.min.js admin.min.js notify.min.js)
CSS = $(addprefix $(DIST)/, main.min.css login.min.css judging.min.css ranking.min.css\
	  timetable.min.css admin.min.css)

default: | $(DIST)
default: $(JS) $(CSS)

$(DIST)/admin.min.js: js/admin.js $(wildcard js/admin-*.js)
	$(ROLLUP) $(ROLLUP_ARGS) -f iife -n admin $<\
		| $(UGLIFYJS) $(UGLIFYJS_ARGS)\
		> $@

$(DIST)/judging.min.js: $(wildcard js/judging-*.js)
$(DIST)/ranking.min.js: $(wildcard js/ranking-*.js)
$(DIST)/%.min.js: js/%.js
	$(ROLLUP) $(ROLLUP_ARGS) -f iife -n $(subst -,_,$*) $<\
		| $(BUBLE) $(BUBLE_ARGS)\
		| $(UGLIFYJS) $(UGLIFYJS_ARGS)\
		> $@

$(DIST)/main.min.css: css/reset.scss css/common.scss css/notify.scss
$(DIST)/judging.min.css: $(wildcard css/judging-*.scss)
$(DIST)/ranking.min.css: $(wildcard css/ranking-*.scss)
$(DIST)/admin.min.css: $(wildcard css/admin-*.scss)
$(DIST)/%.min.css: css/%.scss css/config.scss
	$(SASS) $(SASS_ARGS) $< > $@

watch:
	$(NODEMON) -w js -w css -e js,scss -x make

clean:
	rm -f $(DIST)/*.js $(DIST)/*.css
