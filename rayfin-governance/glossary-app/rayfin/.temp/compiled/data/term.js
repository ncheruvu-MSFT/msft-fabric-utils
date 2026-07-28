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
let Term = (() => {
    let _classDecorators = [entity(), authenticated(['read']), authenticated(['create']), authenticated(['update', 'delete'], {
            policy: (claims, item) => claims.role.eq('steward').or(claims.sub.eq(item.submittedBySub)),
        })];
    let _classDescriptor;
    let _classExtraInitializers = [];
    let _classThis;
    let _id_decorators;
    let _id_initializers = [];
    let _id_extraInitializers = [];
    let _name_decorators;
    let _name_initializers = [];
    let _name_extraInitializers = [];
    let _definition_decorators;
    let _definition_initializers = [];
    let _definition_extraInitializers = [];
    let _domainId_decorators;
    let _domainId_initializers = [];
    let _domainId_extraInitializers = [];
    let _status_decorators;
    let _status_initializers = [];
    let _status_extraInitializers = [];
    let _submittedBySub_decorators;
    let _submittedBySub_initializers = [];
    let _submittedBySub_extraInitializers = [];
    let _approvedBySub_decorators;
    let _approvedBySub_initializers = [];
    let _approvedBySub_extraInitializers = [];
    let _purviewQualifiedName_decorators;
    let _purviewQualifiedName_initializers = [];
    let _purviewQualifiedName_extraInitializers = [];
    let _auditCreatedAt_decorators;
    let _auditCreatedAt_initializers = [];
    let _auditCreatedAt_extraInitializers = [];
    let _auditUpdatedAt_decorators;
    let _auditUpdatedAt_initializers = [];
    let _auditUpdatedAt_extraInitializers = [];
    var Term = class {
        static { _classThis = this; }
        static {
            const _metadata = typeof Symbol === "function" && Symbol.metadata ? Object.create(null) : void 0;
            _id_decorators = [uuid()];
            _name_decorators = [text({ max: 200 })];
            _definition_decorators = [text({ max: 4000 })];
            _domainId_decorators = [text({ max: 200 })];
            _status_decorators = [text({ max: 100 })];
            _submittedBySub_decorators = [text({ max: 200 })];
            _approvedBySub_decorators = [text({ optional: true, max: 200 })];
            _purviewQualifiedName_decorators = [text({ optional: true, max: 400 })];
            _auditCreatedAt_decorators = [date()];
            _auditUpdatedAt_decorators = [date({ optional: true })];
            __esDecorate(null, null, _id_decorators, { kind: "field", name: "id", static: false, private: false, access: { has: obj => "id" in obj, get: obj => obj.id, set: (obj, value) => { obj.id = value; } }, metadata: _metadata }, _id_initializers, _id_extraInitializers);
            __esDecorate(null, null, _name_decorators, { kind: "field", name: "name", static: false, private: false, access: { has: obj => "name" in obj, get: obj => obj.name, set: (obj, value) => { obj.name = value; } }, metadata: _metadata }, _name_initializers, _name_extraInitializers);
            __esDecorate(null, null, _definition_decorators, { kind: "field", name: "definition", static: false, private: false, access: { has: obj => "definition" in obj, get: obj => obj.definition, set: (obj, value) => { obj.definition = value; } }, metadata: _metadata }, _definition_initializers, _definition_extraInitializers);
            __esDecorate(null, null, _domainId_decorators, { kind: "field", name: "domainId", static: false, private: false, access: { has: obj => "domainId" in obj, get: obj => obj.domainId, set: (obj, value) => { obj.domainId = value; } }, metadata: _metadata }, _domainId_initializers, _domainId_extraInitializers);
            __esDecorate(null, null, _status_decorators, { kind: "field", name: "status", static: false, private: false, access: { has: obj => "status" in obj, get: obj => obj.status, set: (obj, value) => { obj.status = value; } }, metadata: _metadata }, _status_initializers, _status_extraInitializers);
            __esDecorate(null, null, _submittedBySub_decorators, { kind: "field", name: "submittedBySub", static: false, private: false, access: { has: obj => "submittedBySub" in obj, get: obj => obj.submittedBySub, set: (obj, value) => { obj.submittedBySub = value; } }, metadata: _metadata }, _submittedBySub_initializers, _submittedBySub_extraInitializers);
            __esDecorate(null, null, _approvedBySub_decorators, { kind: "field", name: "approvedBySub", static: false, private: false, access: { has: obj => "approvedBySub" in obj, get: obj => obj.approvedBySub, set: (obj, value) => { obj.approvedBySub = value; } }, metadata: _metadata }, _approvedBySub_initializers, _approvedBySub_extraInitializers);
            __esDecorate(null, null, _purviewQualifiedName_decorators, { kind: "field", name: "purviewQualifiedName", static: false, private: false, access: { has: obj => "purviewQualifiedName" in obj, get: obj => obj.purviewQualifiedName, set: (obj, value) => { obj.purviewQualifiedName = value; } }, metadata: _metadata }, _purviewQualifiedName_initializers, _purviewQualifiedName_extraInitializers);
            __esDecorate(null, null, _auditCreatedAt_decorators, { kind: "field", name: "auditCreatedAt", static: false, private: false, access: { has: obj => "auditCreatedAt" in obj, get: obj => obj.auditCreatedAt, set: (obj, value) => { obj.auditCreatedAt = value; } }, metadata: _metadata }, _auditCreatedAt_initializers, _auditCreatedAt_extraInitializers);
            __esDecorate(null, null, _auditUpdatedAt_decorators, { kind: "field", name: "auditUpdatedAt", static: false, private: false, access: { has: obj => "auditUpdatedAt" in obj, get: obj => obj.auditUpdatedAt, set: (obj, value) => { obj.auditUpdatedAt = value; } }, metadata: _metadata }, _auditUpdatedAt_initializers, _auditUpdatedAt_extraInitializers);
            __esDecorate(null, _classDescriptor = { value: _classThis }, _classDecorators, { kind: "class", name: _classThis.name, metadata: _metadata }, null, _classExtraInitializers);
            Term = _classThis = _classDescriptor.value;
            if (_metadata) Object.defineProperty(_classThis, Symbol.metadata, { enumerable: true, configurable: true, writable: true, value: _metadata });
            __runInitializers(_classThis, _classExtraInitializers);
        }
        id = __runInitializers(this, _id_initializers, void 0);
        name = (__runInitializers(this, _id_extraInitializers), __runInitializers(this, _name_initializers, void 0));
        definition = (__runInitializers(this, _name_extraInitializers), __runInitializers(this, _definition_initializers, void 0));
        domainId = (__runInitializers(this, _definition_extraInitializers), __runInitializers(this, _domainId_initializers, void 0));
        status = (__runInitializers(this, _domainId_extraInitializers), __runInitializers(this, _status_initializers, void 0));
        submittedBySub = (__runInitializers(this, _status_extraInitializers), __runInitializers(this, _submittedBySub_initializers, void 0));
        approvedBySub = (__runInitializers(this, _submittedBySub_extraInitializers), __runInitializers(this, _approvedBySub_initializers, void 0));
        purviewQualifiedName = (__runInitializers(this, _approvedBySub_extraInitializers), __runInitializers(this, _purviewQualifiedName_initializers, void 0));
        auditCreatedAt = (__runInitializers(this, _purviewQualifiedName_extraInitializers), __runInitializers(this, _auditCreatedAt_initializers, void 0));
        auditUpdatedAt = (__runInitializers(this, _auditCreatedAt_extraInitializers), __runInitializers(this, _auditUpdatedAt_initializers, void 0));
        constructor() {
            __runInitializers(this, _auditUpdatedAt_extraInitializers);
        }
    };
    return Term = _classThis;
})();
export { Term };
