const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
let ext;
const app = {registerExtension(e) { ext = e; }};
const src = fs.readFileSync(path.resolve(__dirname, '../web/js/dynamic_string_list.js'), 'utf8');
vm.runInNewContext(src.replace(/^import \{ app \} from "\/scripts\/app.js";\s*/, ''), {app});
assert.equal(ext.name, 'JR.OpenAIAsk.DynamicStringToList');
const node = {
  comfyClass: 'JRStringToList',
  inputs: [{name:'text_1', link:null}],
  widgets: [],
  addWidget(type,name,value,callback) { this.widgets.push({type,name,callback}); },
  addInput(name,type) { this.inputs.push({name,type,link:null}); },
  removeInput(idx) { this.inputs.splice(idx,1); },
  computeSize() { return [250, 90+20*this.inputs.length]; },
  setSize(size) { this.size=size; },
  setDirtyCanvas() {},
};
ext.nodeCreated(node);
assert.equal(node.widgets.length, 2);
node.widgets[0].callback();
assert.deepEqual(node.inputs.map(x=>x.name), ['text_1','text_2']);
node.inputs[0].link=123;
node.onConnectionsChange(1,0,true);
assert.equal(node.inputs.length,2);
node.inputs[1].link=456;
node.onConnectionsChange(1,1,true);
assert.deepEqual(node.inputs.map(x=>x.name), ['text_1','text_2','text_3']);
node.widgets[1].callback();
assert.deepEqual(node.inputs.map(x=>x.name), ['text_1','text_2']);
node.widgets[1].callback(); // connected; cannot remove
assert.equal(node.inputs.length,2);
node.inputs[1].link=null;
node.widgets[1].callback();
assert.deepEqual(node.inputs.map(x=>x.name), ['text_1']);
ext.nodeCreated(node);
assert.equal(node.widgets.length,2);
console.log('Frontend mock tests passed');
