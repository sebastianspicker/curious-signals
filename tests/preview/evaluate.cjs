// Evaluate the same static fixture script shipped to the browser, without DOM shims.
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");
const source = fs.readFileSync(path.join(__dirname, "../../demo/fixtures.js"), "utf8");
const result = vm.runInNewContext(source + `
JSON.stringify(modes.map(mode => ({
  id: mode.id, series: mode.series,
  units: mode.series.map((_, index) => modeUnit(mode, index)),
  values: fixtures.get(mode.id).series, ranges: fixtures.get(mode.id).ranges,
  cached: fixtures.get(mode.id) === fixtures.get(mode.id),
  frozen: Object.isFrozen(fixtures.get(mode.id).series)
})))`, Object.freeze({}));
process.stdout.write(result);
