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
import { entity, uuid, text, date, authenticated } from '@microsoft/rayfin-core';
// One row per attestation run posted by an ADO pipeline against a workspace.
let AttestationRun = (() => {
    let _classDecorators = [entity(), authenticated(['read']), authenticated(['create'], {
            policy: (claims) => claims.role.eq('pipeline').or(claims.role.eq('governance-admin')),
        }), authenticated(['update', 'delete'], {
            policy: (claims) => claims.role.eq('governance-admin'),
        })];
    let _classDescriptor;
    let _classExtraInitializers = [];
    let _classThis;
    let _id_decorators;
    let _id_initializers = [];
    let _id_extraInitializers = [];
    let _workspaceId_decorators;
    let _workspaceId_initializers = [];
    let _workspaceId_extraInitializers = [];
    let _policyName_decorators;
    let _policyName_initializers = [];
    let _policyName_extraInitializers = [];
    let _result_decorators;
    let _result_initializers = [];
    let _result_extraInitializers = [];
    let _pipelineRunUrl_decorators;
    let _pipelineRunUrl_initializers = [];
    let _pipelineRunUrl_extraInitializers = [];
    let _commitSha_decorators;
    let _commitSha_initializers = [];
    let _commitSha_extraInitializers = [];
    let _submittedBySub_decorators;
    let _submittedBySub_initializers = [];
    let _submittedBySub_extraInitializers = [];
    let _findingsJson_decorators;
    let _findingsJson_initializers = [];
    let _findingsJson_extraInitializers = [];
    let _runAt_decorators;
    let _runAt_initializers = [];
    let _runAt_extraInitializers = [];
    var AttestationRun = class {
        static { _classThis = this; }
        static {
            const _metadata = typeof Symbol === "function" && Symbol.metadata ? Object.create(null) : void 0;
            _id_decorators = [uuid()];
            _workspaceId_decorators = [text({ max: 200 })];
            _policyName_decorators = [text({ max: 200 })];
            _result_decorators = [text({ max: 100 })];
            _pipelineRunUrl_decorators = [text({ max: 400 })];
            _commitSha_decorators = [text({ max: 100 })];
            _submittedBySub_decorators = [text({ max: 200 })];
            _findingsJson_decorators = [text({ optional: true, max: 4000 })];
            _runAt_decorators = [date()];
            __esDecorate(null, null, _id_decorators, { kind: "field", name: "id", static: false, private: false, access: { has: obj => "id" in obj, get: obj => obj.id, set: (obj, value) => { obj.id = value; } }, metadata: _metadata }, _id_initializers, _id_extraInitializers);
            __esDecorate(null, null, _workspaceId_decorators, { kind: "field", name: "workspaceId", static: false, private: false, access: { has: obj => "workspaceId" in obj, get: obj => obj.workspaceId, set: (obj, value) => { obj.workspaceId = value; } }, metadata: _metadata }, _workspaceId_initializers, _workspaceId_extraInitializers);
            __esDecorate(null, null, _policyName_decorators, { kind: "field", name: "policyName", static: false, private: false, access: { has: obj => "policyName" in obj, get: obj => obj.policyName, set: (obj, value) => { obj.policyName = value; } }, metadata: _metadata }, _policyName_initializers, _policyName_extraInitializers);
            __esDecorate(null, null, _result_decorators, { kind: "field", name: "result", static: false, private: false, access: { has: obj => "result" in obj, get: obj => obj.result, set: (obj, value) => { obj.result = value; } }, metadata: _metadata }, _result_initializers, _result_extraInitializers);
            __esDecorate(null, null, _pipelineRunUrl_decorators, { kind: "field", name: "pipelineRunUrl", static: false, private: false, access: { has: obj => "pipelineRunUrl" in obj, get: obj => obj.pipelineRunUrl, set: (obj, value) => { obj.pipelineRunUrl = value; } }, metadata: _metadata }, _pipelineRunUrl_initializers, _pipelineRunUrl_extraInitializers);
            __esDecorate(null, null, _commitSha_decorators, { kind: "field", name: "commitSha", static: false, private: false, access: { has: obj => "commitSha" in obj, get: obj => obj.commitSha, set: (obj, value) => { obj.commitSha = value; } }, metadata: _metadata }, _commitSha_initializers, _commitSha_extraInitializers);
            __esDecorate(null, null, _submittedBySub_decorators, { kind: "field", name: "submittedBySub", static: false, private: false, access: { has: obj => "submittedBySub" in obj, get: obj => obj.submittedBySub, set: (obj, value) => { obj.submittedBySub = value; } }, metadata: _metadata }, _submittedBySub_initializers, _submittedBySub_extraInitializers);
            __esDecorate(null, null, _findingsJson_decorators, { kind: "field", name: "findingsJson", static: false, private: false, access: { has: obj => "findingsJson" in obj, get: obj => obj.findingsJson, set: (obj, value) => { obj.findingsJson = value; } }, metadata: _metadata }, _findingsJson_initializers, _findingsJson_extraInitializers);
            __esDecorate(null, null, _runAt_decorators, { kind: "field", name: "runAt", static: false, private: false, access: { has: obj => "runAt" in obj, get: obj => obj.runAt, set: (obj, value) => { obj.runAt = value; } }, metadata: _metadata }, _runAt_initializers, _runAt_extraInitializers);
            __esDecorate(null, _classDescriptor = { value: _classThis }, _classDecorators, { kind: "class", name: _classThis.name, metadata: _metadata }, null, _classExtraInitializers);
            AttestationRun = _classThis = _classDescriptor.value;
            if (_metadata) Object.defineProperty(_classThis, Symbol.metadata, { enumerable: true, configurable: true, writable: true, value: _metadata });
            __runInitializers(_classThis, _classExtraInitializers);
        }
        id = __runInitializers(this, _id_initializers, void 0);
        workspaceId = (__runInitializers(this, _id_extraInitializers), __runInitializers(this, _workspaceId_initializers, void 0));
        policyName = (__runInitializers(this, _workspaceId_extraInitializers), __runInitializers(this, _policyName_initializers, void 0));
        result = (__runInitializers(this, _policyName_extraInitializers), __runInitializers(this, _result_initializers, void 0));
        pipelineRunUrl = (__runInitializers(this, _result_extraInitializers), __runInitializers(this, _pipelineRunUrl_initializers, void 0));
        commitSha = (__runInitializers(this, _pipelineRunUrl_extraInitializers), __runInitializers(this, _commitSha_initializers, void 0));
        submittedBySub = (__runInitializers(this, _commitSha_extraInitializers), __runInitializers(this, _submittedBySub_initializers, void 0));
        findingsJson = (__runInitializers(this, _submittedBySub_extraInitializers), __runInitializers(this, _findingsJson_initializers, void 0));
        runAt = (__runInitializers(this, _findingsJson_extraInitializers), __runInitializers(this, _runAt_initializers, void 0));
        constructor() {
            __runInitializers(this, _runAt_extraInitializers);
        }
    };
    return AttestationRun = _classThis;
})();
export { AttestationRun };
