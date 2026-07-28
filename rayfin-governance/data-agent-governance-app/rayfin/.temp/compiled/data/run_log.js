var __esDecorate = (this && this.__esDecorate) || function (ctor, descriptorIn, decorators, contextIn, initializers, extraInitializers) {
    function accept(f) { if (f !== void 0 && typeof f !== "function") throw new TypeError("Function expected"); return f; }
    var kind = contextIn.kind, key = kind === "getter" ? "get" : kind === "setter" ? "set" : "value";
    var target = !descriptorIn && ctor ? contextIn["static"] ? ctor : ctor.prototype : null;
    var descriptor = descriptorIn || (target ? Object.getOwnPropertyDescriptor(target, contextIn.name) : {});
    var _, done = false;
    for (var i = decorators.length - 1; i >= 0; i--) {
        var context = {};
        for (var p in contextIn) context[p] = p === "access" ? {} : contextIn[p];
        for (var p in contextIn.access) context.access[p] = contextIn.access[p];
        context.addInitializer = function (f) { if (done) throw new TypeError("Cannot add initializers after decoration has completed"); extraInitializers.push(accept(f || null)); };
        var result = (0, decorators[i])(kind === "accessor" ? { get: descriptor.get, set: descriptor.set } : descriptor[key], context);
        if (kind === "accessor") {
            if (result === void 0) continue;
            if (result === null || typeof result !== "object") throw new TypeError("Object expected");
            if (_ = accept(result.get)) descriptor.get = _;
            if (_ = accept(result.set)) descriptor.set = _;
            if (_ = accept(result.init)) initializers.unshift(_);
        }
        else if (_ = accept(result)) {
            if (kind === "field") initializers.unshift(_);
            else descriptor[key] = _;
        }
    }
    if (target) Object.defineProperty(target, contextIn.name, descriptor);
    done = true;
};
var __runInitializers = (this && this.__runInitializers) || function (thisArg, initializers, value) {
    var useValue = arguments.length > 2;
    for (var i = 0; i < initializers.length; i++) {
        value = useValue ? initializers[i].call(thisArg, value) : initializers[i].call(thisArg);
    }
    return useValue ? value : void 0;
};
import { entity, uuid, text, int, date, authenticated } from '@microsoft/rayfin-core';
// Append-only. Agent runtimes POST here.
let RunLog = (() => {
    let _classDecorators = [entity(), authenticated(['read']), authenticated(['create'], {
            policy: (claims) => claims.role.eq('agent-runtime').or(claims.role.eq('agent-admin')),
        }), authenticated(['delete'], {
            policy: (claims) => claims.role.eq('agent-admin'),
        })];
    let _classDescriptor;
    let _classExtraInitializers = [];
    let _classThis;
    let _id_decorators;
    let _id_initializers = [];
    let _id_extraInitializers = [];
    let _agentId_decorators;
    let _agentId_initializers = [];
    let _agentId_extraInitializers = [];
    let _promptTemplateId_decorators;
    let _promptTemplateId_initializers = [];
    let _promptTemplateId_extraInitializers = [];
    let _callerSub_decorators;
    let _callerSub_initializers = [];
    let _callerSub_extraInitializers = [];
    let _status_decorators;
    let _status_initializers = [];
    let _status_extraInitializers = [];
    let _inputTokens_decorators;
    let _inputTokens_initializers = [];
    let _inputTokens_extraInitializers = [];
    let _outputTokens_decorators;
    let _outputTokens_initializers = [];
    let _outputTokens_extraInitializers = [];
    let _toolCallsJson_decorators;
    let _toolCallsJson_initializers = [];
    let _toolCallsJson_extraInitializers = [];
    let _redactedInput_decorators;
    let _redactedInput_initializers = [];
    let _redactedInput_extraInitializers = [];
    let _redactedOutput_decorators;
    let _redactedOutput_initializers = [];
    let _redactedOutput_extraInitializers = [];
    let _startedAt_decorators;
    let _startedAt_initializers = [];
    let _startedAt_extraInitializers = [];
    let _finishedAt_decorators;
    let _finishedAt_initializers = [];
    let _finishedAt_extraInitializers = [];
    var RunLog = class {
        static { _classThis = this; }
        static {
            const _metadata = typeof Symbol === "function" && Symbol.metadata ? Object.create(null) : void 0;
            _id_decorators = [uuid()];
            _agentId_decorators = [text({ max: 200 })];
            _promptTemplateId_decorators = [text({ max: 200 })];
            _callerSub_decorators = [text({ max: 200 })];
            _status_decorators = [text({ max: 100 })];
            _inputTokens_decorators = [int()];
            _outputTokens_decorators = [int()];
            _toolCallsJson_decorators = [text({ optional: true, max: 4000 })];
            _redactedInput_decorators = [text({ optional: true, max: 4000 })];
            _redactedOutput_decorators = [text({ optional: true, max: 4000 })];
            _startedAt_decorators = [date()];
            _finishedAt_decorators = [date()];
            __esDecorate(null, null, _id_decorators, { kind: "field", name: "id", static: false, private: false, access: { has: obj => "id" in obj, get: obj => obj.id, set: (obj, value) => { obj.id = value; } }, metadata: _metadata }, _id_initializers, _id_extraInitializers);
            __esDecorate(null, null, _agentId_decorators, { kind: "field", name: "agentId", static: false, private: false, access: { has: obj => "agentId" in obj, get: obj => obj.agentId, set: (obj, value) => { obj.agentId = value; } }, metadata: _metadata }, _agentId_initializers, _agentId_extraInitializers);
            __esDecorate(null, null, _promptTemplateId_decorators, { kind: "field", name: "promptTemplateId", static: false, private: false, access: { has: obj => "promptTemplateId" in obj, get: obj => obj.promptTemplateId, set: (obj, value) => { obj.promptTemplateId = value; } }, metadata: _metadata }, _promptTemplateId_initializers, _promptTemplateId_extraInitializers);
            __esDecorate(null, null, _callerSub_decorators, { kind: "field", name: "callerSub", static: false, private: false, access: { has: obj => "callerSub" in obj, get: obj => obj.callerSub, set: (obj, value) => { obj.callerSub = value; } }, metadata: _metadata }, _callerSub_initializers, _callerSub_extraInitializers);
            __esDecorate(null, null, _status_decorators, { kind: "field", name: "status", static: false, private: false, access: { has: obj => "status" in obj, get: obj => obj.status, set: (obj, value) => { obj.status = value; } }, metadata: _metadata }, _status_initializers, _status_extraInitializers);
            __esDecorate(null, null, _inputTokens_decorators, { kind: "field", name: "inputTokens", static: false, private: false, access: { has: obj => "inputTokens" in obj, get: obj => obj.inputTokens, set: (obj, value) => { obj.inputTokens = value; } }, metadata: _metadata }, _inputTokens_initializers, _inputTokens_extraInitializers);
            __esDecorate(null, null, _outputTokens_decorators, { kind: "field", name: "outputTokens", static: false, private: false, access: { has: obj => "outputTokens" in obj, get: obj => obj.outputTokens, set: (obj, value) => { obj.outputTokens = value; } }, metadata: _metadata }, _outputTokens_initializers, _outputTokens_extraInitializers);
            __esDecorate(null, null, _toolCallsJson_decorators, { kind: "field", name: "toolCallsJson", static: false, private: false, access: { has: obj => "toolCallsJson" in obj, get: obj => obj.toolCallsJson, set: (obj, value) => { obj.toolCallsJson = value; } }, metadata: _metadata }, _toolCallsJson_initializers, _toolCallsJson_extraInitializers);
            __esDecorate(null, null, _redactedInput_decorators, { kind: "field", name: "redactedInput", static: false, private: false, access: { has: obj => "redactedInput" in obj, get: obj => obj.redactedInput, set: (obj, value) => { obj.redactedInput = value; } }, metadata: _metadata }, _redactedInput_initializers, _redactedInput_extraInitializers);
            __esDecorate(null, null, _redactedOutput_decorators, { kind: "field", name: "redactedOutput", static: false, private: false, access: { has: obj => "redactedOutput" in obj, get: obj => obj.redactedOutput, set: (obj, value) => { obj.redactedOutput = value; } }, metadata: _metadata }, _redactedOutput_initializers, _redactedOutput_extraInitializers);
            __esDecorate(null, null, _startedAt_decorators, { kind: "field", name: "startedAt", static: false, private: false, access: { has: obj => "startedAt" in obj, get: obj => obj.startedAt, set: (obj, value) => { obj.startedAt = value; } }, metadata: _metadata }, _startedAt_initializers, _startedAt_extraInitializers);
            __esDecorate(null, null, _finishedAt_decorators, { kind: "field", name: "finishedAt", static: false, private: false, access: { has: obj => "finishedAt" in obj, get: obj => obj.finishedAt, set: (obj, value) => { obj.finishedAt = value; } }, metadata: _metadata }, _finishedAt_initializers, _finishedAt_extraInitializers);
            __esDecorate(null, _classDescriptor = { value: _classThis }, _classDecorators, { kind: "class", name: _classThis.name, metadata: _metadata }, null, _classExtraInitializers);
            RunLog = _classThis = _classDescriptor.value;
            if (_metadata) Object.defineProperty(_classThis, Symbol.metadata, { enumerable: true, configurable: true, writable: true, value: _metadata });
            __runInitializers(_classThis, _classExtraInitializers);
        }
        id = __runInitializers(this, _id_initializers, void 0);
        agentId = (__runInitializers(this, _id_extraInitializers), __runInitializers(this, _agentId_initializers, void 0));
        promptTemplateId = (__runInitializers(this, _agentId_extraInitializers), __runInitializers(this, _promptTemplateId_initializers, void 0));
        callerSub = (__runInitializers(this, _promptTemplateId_extraInitializers), __runInitializers(this, _callerSub_initializers, void 0));
        status = (__runInitializers(this, _callerSub_extraInitializers), __runInitializers(this, _status_initializers, void 0));
        inputTokens = (__runInitializers(this, _status_extraInitializers), __runInitializers(this, _inputTokens_initializers, void 0));
        outputTokens = (__runInitializers(this, _inputTokens_extraInitializers), __runInitializers(this, _outputTokens_initializers, void 0));
        toolCallsJson = (__runInitializers(this, _outputTokens_extraInitializers), __runInitializers(this, _toolCallsJson_initializers, void 0));
        redactedInput = (__runInitializers(this, _toolCallsJson_extraInitializers), __runInitializers(this, _redactedInput_initializers, void 0));
        redactedOutput = (__runInitializers(this, _redactedInput_extraInitializers), __runInitializers(this, _redactedOutput_initializers, void 0));
        startedAt = (__runInitializers(this, _redactedOutput_extraInitializers), __runInitializers(this, _startedAt_initializers, void 0));
        finishedAt = (__runInitializers(this, _startedAt_extraInitializers), __runInitializers(this, _finishedAt_initializers, void 0));
        constructor() {
            __runInitializers(this, _finishedAt_extraInitializers);
        }
    };
    return RunLog = _classThis;
})();
export { RunLog };
