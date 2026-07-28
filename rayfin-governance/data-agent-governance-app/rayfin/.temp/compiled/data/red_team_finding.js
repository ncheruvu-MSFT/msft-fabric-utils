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
let RedTeamFinding = (() => {
    let _classDecorators = [entity(), authenticated(['read']), authenticated(['create'], {
            policy: (claims) => claims.role.eq('red-team').or(claims.role.eq('agent-admin')),
        }), authenticated(['update'], {
            policy: (claims, item) => claims.role.eq('agent-admin').or(claims.sub.eq(item.assigneeSub)),
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
    let _severity_decorators;
    let _severity_initializers = [];
    let _severity_extraInitializers = [];
    let _category_decorators;
    let _category_initializers = [];
    let _category_extraInitializers = [];
    let _title_decorators;
    let _title_initializers = [];
    let _title_extraInitializers = [];
    let _description_decorators;
    let _description_initializers = [];
    let _description_extraInitializers = [];
    let _status_decorators;
    let _status_initializers = [];
    let _status_extraInitializers = [];
    let _reporterSub_decorators;
    let _reporterSub_initializers = [];
    let _reporterSub_extraInitializers = [];
    let _assigneeSub_decorators;
    let _assigneeSub_initializers = [];
    let _assigneeSub_extraInitializers = [];
    let _mitigationNote_decorators;
    let _mitigationNote_initializers = [];
    let _mitigationNote_extraInitializers = [];
    let _reportedAt_decorators;
    let _reportedAt_initializers = [];
    let _reportedAt_extraInitializers = [];
    let _resolvedAt_decorators;
    let _resolvedAt_initializers = [];
    let _resolvedAt_extraInitializers = [];
    var RedTeamFinding = class {
        static { _classThis = this; }
        static {
            const _metadata = typeof Symbol === "function" && Symbol.metadata ? Object.create(null) : void 0;
            _id_decorators = [uuid()];
            _agentId_decorators = [text({ max: 200 })];
            _severity_decorators = [text({ max: 100 })];
            _category_decorators = [text({ max: 100 })];
            _title_decorators = [text({ max: 200 })];
            _description_decorators = [text({ max: 4000 })];
            _status_decorators = [text({ max: 100 })];
            _reporterSub_decorators = [text({ max: 200 })];
            _assigneeSub_decorators = [text({ optional: true, max: 200 })];
            _mitigationNote_decorators = [text({ optional: true, max: 4000 })];
            _reportedAt_decorators = [date()];
            _resolvedAt_decorators = [date({ optional: true })];
            __esDecorate(null, null, _id_decorators, { kind: "field", name: "id", static: false, private: false, access: { has: obj => "id" in obj, get: obj => obj.id, set: (obj, value) => { obj.id = value; } }, metadata: _metadata }, _id_initializers, _id_extraInitializers);
            __esDecorate(null, null, _agentId_decorators, { kind: "field", name: "agentId", static: false, private: false, access: { has: obj => "agentId" in obj, get: obj => obj.agentId, set: (obj, value) => { obj.agentId = value; } }, metadata: _metadata }, _agentId_initializers, _agentId_extraInitializers);
            __esDecorate(null, null, _severity_decorators, { kind: "field", name: "severity", static: false, private: false, access: { has: obj => "severity" in obj, get: obj => obj.severity, set: (obj, value) => { obj.severity = value; } }, metadata: _metadata }, _severity_initializers, _severity_extraInitializers);
            __esDecorate(null, null, _category_decorators, { kind: "field", name: "category", static: false, private: false, access: { has: obj => "category" in obj, get: obj => obj.category, set: (obj, value) => { obj.category = value; } }, metadata: _metadata }, _category_initializers, _category_extraInitializers);
            __esDecorate(null, null, _title_decorators, { kind: "field", name: "title", static: false, private: false, access: { has: obj => "title" in obj, get: obj => obj.title, set: (obj, value) => { obj.title = value; } }, metadata: _metadata }, _title_initializers, _title_extraInitializers);
            __esDecorate(null, null, _description_decorators, { kind: "field", name: "description", static: false, private: false, access: { has: obj => "description" in obj, get: obj => obj.description, set: (obj, value) => { obj.description = value; } }, metadata: _metadata }, _description_initializers, _description_extraInitializers);
            __esDecorate(null, null, _status_decorators, { kind: "field", name: "status", static: false, private: false, access: { has: obj => "status" in obj, get: obj => obj.status, set: (obj, value) => { obj.status = value; } }, metadata: _metadata }, _status_initializers, _status_extraInitializers);
            __esDecorate(null, null, _reporterSub_decorators, { kind: "field", name: "reporterSub", static: false, private: false, access: { has: obj => "reporterSub" in obj, get: obj => obj.reporterSub, set: (obj, value) => { obj.reporterSub = value; } }, metadata: _metadata }, _reporterSub_initializers, _reporterSub_extraInitializers);
            __esDecorate(null, null, _assigneeSub_decorators, { kind: "field", name: "assigneeSub", static: false, private: false, access: { has: obj => "assigneeSub" in obj, get: obj => obj.assigneeSub, set: (obj, value) => { obj.assigneeSub = value; } }, metadata: _metadata }, _assigneeSub_initializers, _assigneeSub_extraInitializers);
            __esDecorate(null, null, _mitigationNote_decorators, { kind: "field", name: "mitigationNote", static: false, private: false, access: { has: obj => "mitigationNote" in obj, get: obj => obj.mitigationNote, set: (obj, value) => { obj.mitigationNote = value; } }, metadata: _metadata }, _mitigationNote_initializers, _mitigationNote_extraInitializers);
            __esDecorate(null, null, _reportedAt_decorators, { kind: "field", name: "reportedAt", static: false, private: false, access: { has: obj => "reportedAt" in obj, get: obj => obj.reportedAt, set: (obj, value) => { obj.reportedAt = value; } }, metadata: _metadata }, _reportedAt_initializers, _reportedAt_extraInitializers);
            __esDecorate(null, null, _resolvedAt_decorators, { kind: "field", name: "resolvedAt", static: false, private: false, access: { has: obj => "resolvedAt" in obj, get: obj => obj.resolvedAt, set: (obj, value) => { obj.resolvedAt = value; } }, metadata: _metadata }, _resolvedAt_initializers, _resolvedAt_extraInitializers);
            __esDecorate(null, _classDescriptor = { value: _classThis }, _classDecorators, { kind: "class", name: _classThis.name, metadata: _metadata }, null, _classExtraInitializers);
            RedTeamFinding = _classThis = _classDescriptor.value;
            if (_metadata) Object.defineProperty(_classThis, Symbol.metadata, { enumerable: true, configurable: true, writable: true, value: _metadata });
            __runInitializers(_classThis, _classExtraInitializers);
        }
        id = __runInitializers(this, _id_initializers, void 0);
        agentId = (__runInitializers(this, _id_extraInitializers), __runInitializers(this, _agentId_initializers, void 0));
        severity = (__runInitializers(this, _agentId_extraInitializers), __runInitializers(this, _severity_initializers, void 0));
        category = (__runInitializers(this, _severity_extraInitializers), __runInitializers(this, _category_initializers, void 0));
        title = (__runInitializers(this, _category_extraInitializers), __runInitializers(this, _title_initializers, void 0));
        description = (__runInitializers(this, _title_extraInitializers), __runInitializers(this, _description_initializers, void 0));
        status = (__runInitializers(this, _description_extraInitializers), __runInitializers(this, _status_initializers, void 0));
        reporterSub = (__runInitializers(this, _status_extraInitializers), __runInitializers(this, _reporterSub_initializers, void 0));
        assigneeSub = (__runInitializers(this, _reporterSub_extraInitializers), __runInitializers(this, _assigneeSub_initializers, void 0));
        mitigationNote = (__runInitializers(this, _assigneeSub_extraInitializers), __runInitializers(this, _mitigationNote_initializers, void 0));
        reportedAt = (__runInitializers(this, _mitigationNote_extraInitializers), __runInitializers(this, _reportedAt_initializers, void 0));
        resolvedAt = (__runInitializers(this, _reportedAt_extraInitializers), __runInitializers(this, _resolvedAt_initializers, void 0));
        constructor() {
            __runInitializers(this, _resolvedAt_extraInitializers);
        }
    };
    return RedTeamFinding = _classThis;
})();
export { RedTeamFinding };
