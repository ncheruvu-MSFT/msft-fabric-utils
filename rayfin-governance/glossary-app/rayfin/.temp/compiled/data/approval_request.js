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
let ApprovalRequest = (() => {
    let _classDecorators = [entity(), authenticated(['create', 'read']), authenticated(['update'], {
            policy: (claims, item) => claims.role.eq('steward').or(claims.sub.eq(item.assigneeSub)),
        })];
    let _classDescriptor;
    let _classExtraInitializers = [];
    let _classThis;
    let _id_decorators;
    let _id_initializers = [];
    let _id_extraInitializers = [];
    let _targetType_decorators;
    let _targetType_initializers = [];
    let _targetType_extraInitializers = [];
    let _targetId_decorators;
    let _targetId_initializers = [];
    let _targetId_extraInitializers = [];
    let _workflowName_decorators;
    let _workflowName_initializers = [];
    let _workflowName_extraInitializers = [];
    let _status_decorators;
    let _status_initializers = [];
    let _status_extraInitializers = [];
    let _requesterSub_decorators;
    let _requesterSub_initializers = [];
    let _requesterSub_extraInitializers = [];
    let _assigneeSub_decorators;
    let _assigneeSub_initializers = [];
    let _assigneeSub_extraInitializers = [];
    let _decisionNote_decorators;
    let _decisionNote_initializers = [];
    let _decisionNote_extraInitializers = [];
    let _auditCreatedAt_decorators;
    let _auditCreatedAt_initializers = [];
    let _auditCreatedAt_extraInitializers = [];
    let _decidedAt_decorators;
    let _decidedAt_initializers = [];
    let _decidedAt_extraInitializers = [];
    var ApprovalRequest = class {
        static { _classThis = this; }
        static {
            const _metadata = typeof Symbol === "function" && Symbol.metadata ? Object.create(null) : void 0;
            _id_decorators = [uuid()];
            _targetType_decorators = [text({ max: 100 })];
            _targetId_decorators = [text({ max: 200 })];
            _workflowName_decorators = [text({ max: 200 })];
            _status_decorators = [text({ max: 100 })];
            _requesterSub_decorators = [text({ max: 200 })];
            _assigneeSub_decorators = [text({ optional: true, max: 200 })];
            _decisionNote_decorators = [text({ optional: true, max: 4000 })];
            _auditCreatedAt_decorators = [date()];
            _decidedAt_decorators = [date({ optional: true })];
            __esDecorate(null, null, _id_decorators, { kind: "field", name: "id", static: false, private: false, access: { has: obj => "id" in obj, get: obj => obj.id, set: (obj, value) => { obj.id = value; } }, metadata: _metadata }, _id_initializers, _id_extraInitializers);
            __esDecorate(null, null, _targetType_decorators, { kind: "field", name: "targetType", static: false, private: false, access: { has: obj => "targetType" in obj, get: obj => obj.targetType, set: (obj, value) => { obj.targetType = value; } }, metadata: _metadata }, _targetType_initializers, _targetType_extraInitializers);
            __esDecorate(null, null, _targetId_decorators, { kind: "field", name: "targetId", static: false, private: false, access: { has: obj => "targetId" in obj, get: obj => obj.targetId, set: (obj, value) => { obj.targetId = value; } }, metadata: _metadata }, _targetId_initializers, _targetId_extraInitializers);
            __esDecorate(null, null, _workflowName_decorators, { kind: "field", name: "workflowName", static: false, private: false, access: { has: obj => "workflowName" in obj, get: obj => obj.workflowName, set: (obj, value) => { obj.workflowName = value; } }, metadata: _metadata }, _workflowName_initializers, _workflowName_extraInitializers);
            __esDecorate(null, null, _status_decorators, { kind: "field", name: "status", static: false, private: false, access: { has: obj => "status" in obj, get: obj => obj.status, set: (obj, value) => { obj.status = value; } }, metadata: _metadata }, _status_initializers, _status_extraInitializers);
            __esDecorate(null, null, _requesterSub_decorators, { kind: "field", name: "requesterSub", static: false, private: false, access: { has: obj => "requesterSub" in obj, get: obj => obj.requesterSub, set: (obj, value) => { obj.requesterSub = value; } }, metadata: _metadata }, _requesterSub_initializers, _requesterSub_extraInitializers);
            __esDecorate(null, null, _assigneeSub_decorators, { kind: "field", name: "assigneeSub", static: false, private: false, access: { has: obj => "assigneeSub" in obj, get: obj => obj.assigneeSub, set: (obj, value) => { obj.assigneeSub = value; } }, metadata: _metadata }, _assigneeSub_initializers, _assigneeSub_extraInitializers);
            __esDecorate(null, null, _decisionNote_decorators, { kind: "field", name: "decisionNote", static: false, private: false, access: { has: obj => "decisionNote" in obj, get: obj => obj.decisionNote, set: (obj, value) => { obj.decisionNote = value; } }, metadata: _metadata }, _decisionNote_initializers, _decisionNote_extraInitializers);
            __esDecorate(null, null, _auditCreatedAt_decorators, { kind: "field", name: "auditCreatedAt", static: false, private: false, access: { has: obj => "auditCreatedAt" in obj, get: obj => obj.auditCreatedAt, set: (obj, value) => { obj.auditCreatedAt = value; } }, metadata: _metadata }, _auditCreatedAt_initializers, _auditCreatedAt_extraInitializers);
            __esDecorate(null, null, _decidedAt_decorators, { kind: "field", name: "decidedAt", static: false, private: false, access: { has: obj => "decidedAt" in obj, get: obj => obj.decidedAt, set: (obj, value) => { obj.decidedAt = value; } }, metadata: _metadata }, _decidedAt_initializers, _decidedAt_extraInitializers);
            __esDecorate(null, _classDescriptor = { value: _classThis }, _classDecorators, { kind: "class", name: _classThis.name, metadata: _metadata }, null, _classExtraInitializers);
            ApprovalRequest = _classThis = _classDescriptor.value;
            if (_metadata) Object.defineProperty(_classThis, Symbol.metadata, { enumerable: true, configurable: true, writable: true, value: _metadata });
            __runInitializers(_classThis, _classExtraInitializers);
        }
        id = __runInitializers(this, _id_initializers, void 0);
        targetType = (__runInitializers(this, _id_extraInitializers), __runInitializers(this, _targetType_initializers, void 0));
        targetId = (__runInitializers(this, _targetType_extraInitializers), __runInitializers(this, _targetId_initializers, void 0));
        workflowName = (__runInitializers(this, _targetId_extraInitializers), __runInitializers(this, _workflowName_initializers, void 0));
        status = (__runInitializers(this, _workflowName_extraInitializers), __runInitializers(this, _status_initializers, void 0));
        requesterSub = (__runInitializers(this, _status_extraInitializers), __runInitializers(this, _requesterSub_initializers, void 0));
        assigneeSub = (__runInitializers(this, _requesterSub_extraInitializers), __runInitializers(this, _assigneeSub_initializers, void 0));
        decisionNote = (__runInitializers(this, _assigneeSub_extraInitializers), __runInitializers(this, _decisionNote_initializers, void 0));
        auditCreatedAt = (__runInitializers(this, _decisionNote_extraInitializers), __runInitializers(this, _auditCreatedAt_initializers, void 0));
        decidedAt = (__runInitializers(this, _auditCreatedAt_extraInitializers), __runInitializers(this, _decidedAt_initializers, void 0));
        constructor() {
            __runInitializers(this, _decidedAt_extraInitializers);
        }
    };
    return ApprovalRequest = _classThis;
})();
export { ApprovalRequest };
