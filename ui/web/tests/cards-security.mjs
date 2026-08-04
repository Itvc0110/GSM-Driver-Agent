import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";

const source = await readFile(new URL("../js/cards.js", import.meta.url), "utf8");
assert.doesNotMatch(source, /innerHTML/);
