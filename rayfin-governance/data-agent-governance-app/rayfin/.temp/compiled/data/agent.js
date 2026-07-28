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
import { entity, uuid, text, boolean, date, authenticated } from '@microsoft/rayfin-core';
let Agent = (() => {
    let _classDecorators = [entity(), authenticated(['read']), authenticated(['create', 'update'], {
            policy: (claims, item) => claims.role.eq('agent-author').or(claims.sub.eq(item.ownerSub)),
        }), authenticated(['delete'], {
            policy: (claims) => claims.role.eq('agent-admin'),
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
    let _description_decorators;
    let _description_initializers = [];
    let _description_extraInitializers = [];
    let _domainId_decorators;
    let _domainId_initializers = [];
    let _domainId_extraInitializers = [];
    let _ownerSub_decorators;
    let _ownerSub_initializers = [];
    let _ownerSub_extraInitializers = [];
    let _status_decorators;
    let _status_initializers = [];
    let _status_extraInitializers = [];
    let _modelDeployment_decorators;
    let _modelDeployment_initializers = [];
    let _modelDeployment_extraInitializers = [];
    let _requiresHumanApproval_decorators;
    let _requiresHumanApproval_initializers = [];
    let _requiresHumanApproval_extraInitializers = [];
    let _auditCreatedAt_decorators;
    let _auditCreatedAt_initializers = [];
    let _auditCreatedAt_extraInitializers = [];
    let _auditUpdatedAt_decorators;
    let _auditUpdatedAt_initializers = [];
    let _auditUpdatedAt_extraInitializers = [];
    var Agent = class {
        static { _classThis = this; }
        static {
            const _metadata = typeof Symbol === "function" && Symbol.metadata ? Object.create(null) : void 0;
            _id_decorators = [uuid()];
            _name_decorators = [text({ max: 200 })];
            _description_decorators = [text({ max: 4000 })];
            _domainId_decorators = [text({ max: 200 })];
            _ownerSub_decorators = [text({ max: 200 })];
            _status_decorators = [text({ max: 100 })];
            _modelDeployment_decorators = [text({ max: 200 })];
            _requiresHumanApproval_decorators = [boolean()];
            _auditCreatedAt_decorators = [date()];
            _auditUpdatedAt_decorators = [date({ optional: true })];
            __esDecorate(null, null, _id_decorators, { kind: "field", name: "id", static: false, private: false, access: { has: obj => "id" in obj, get: obj => obj.id, set: (obj, value) => { obj.id = value; } }, metadata: _metadata }, _id_initializers, _id_extraInitializers);
            __esDecorate(null, null, _name_decorators, { kind: "field", name: "name", static: false, private: false, access: { has: obj => "name" in obj, get: obj => obj.name, set: (obj, value) => { obj.name = value; } }, metadata: _metadata }, _name_initializers, _name_extraInitializers);
            __esDecorate(null, null, _description_decorators, { kind: "field", name: "description", static: false, private: false, access: { has: obj => "description" in obj, get: obj => obj.description, set: (obj, value) => { obj.description = value; } }, metadata: _metadata }, _description_initializers, _description_extraInitializers);
            __esDecorate(null, null, _domainId_decorators, { kind: "field", name: "domainId", static: false, private: false, access: { has: obj => "domainId" in obj, get: obj => obj.domainId, set: (obj, value) => { obj.domainId = value; } }, metadata: _metadata }, _domainId_initializers, _domainId_extraInitializers);
            __esDecorate(null, null, _ownerSub_decorators, { kind: "field", name: "ownerSub", static: false, private: false, access: { has: obj => "ownerSub" in obj, get: obj => obj.ownerSub, set: (obj, value) => { obj.ownerSub = value; } }, metadata: _metadata }, _ownerSub_initializers, _ownerSub_extraInitializers);
            __esDecorate(null, null, _status_decorators, { kind: "field", name: "status", static: false, private: false, access: { has: obj => "status" in obj, get: obj => obj.status, set: (obj, value) => { obj.status = value; } }, metadata: _metadata }, _status_initializers, _status_extraInitializers);
            __esDecorate(null, null, _modelDeployment_decorators, { kind: "field", name: "modelDeployment", static: false, private: false, access: { has: obj => "modelDeployment" in obj, get: obj => obj.modelDeployment, set: (obj, value) => { obj.modelDeployment = value; } }, metadata: _metadata }, _modelDeployment_initializers, _modelDeployment_extraInitializers);
            __esDecorate(null, null, _requiresHumanApproval_decorators, { kind: "field", name: "requiresHumanApproval", static: false, private: false, access: { has: obj => "requiresHumanApproval" in obj, get: obj => obj.requiresHumanApproval, set: (obj, value) => { obj.requiresHumanApproval = value; } }, metadata: _metadata }, _requiresHumanApproval_initializers, _requiresHumanApproval_extraInitializers);
            __esDecorate(null, null, _auditCreatedAt_decorators, { kind: "field", name: "auditCreatedAt", static: false, private: false, access: { has: obj => "auditCreatedAt" in obj, get: obj => obj.auditCreatedAt, set: (obj, value) => { obj.auditCreatedAt = value; } }, metadata: _metadata }, _auditCreatedAt_initializers, _auditCreatedAt_extraInitializers);
            __esDecorate(null, null, _auditUpdatedAt_decorators, { kind: "field", name: "auditUpdatedAt", static: false, private: false, access: { has: obj => "auditUpdatedAt" in obj, get: obj => obj.auditUpdatedAt, set: (obj, value) => { obj.auditUpdatedAt = value; } }, metadata: _metadata }, _auditUpdatedAt_initializers, _auditUpdatedAt_extraInitializers);
            __esDecorate(null, _classDescriptor = { value: _classThis }, _classDecorators, { kind: "class", name: _classThis.name, metadata: _metadata }, null, _classExtraInitializers);
            Agent = _classThis = _classDescriptor.value;
            if (_metadata) Object.defineProperty(_classThis, Symbol.metadata, { enumerable: true, configurable: true, writable: true, value: _metadata });
            __runInitializers(_classThis, _classExtraInitializers);
        }
        id = __runInitializers(this, _id_initializers, void 0);
        name = (__runInitializers(this, _id_extraInitializers), __runInitializers(this, _name_initializers, void 0));
        description = (__runInitializers(this, _name_extraInitializers), __runInitializers(this, _description_initializers, void 0));
        domainId = (__runInitializers(this, _description_extraInitializers), __runInitializers(this, _domainId_initializers, void 0));
        ownerSub = (__runInitializers(this, _domainId_extraInitializers), __runInitializers(this, _ownerSub_initializers, void 0));
        status = (__runInitializers(this, _ownerSub_extraInitializers), __runInitializers(this, _status_initializers, void 0));
        modelDeployment = (__runInitializers(this, _status_extraInitializers), __runInitializers(this, _modelDeployment_initializers, void 0));
        requiresHumanApproval = (__runInitializers(this, _modelDeployment_extraInitializers), __runInitializers(this, _requiresHumanApproval_initializers, void 0));
        auditCreatedAt = (__runInitializers(this, _requiresHumanApproval_extraInitializers), __runInitializers(this, _auditCreatedAt_initializers, void 0));
        auditUpdatedAt = (__runInitializers(this, _auditCreatedAt_extraInitializers), __runInitializers(this, _auditUpdatedAt_initializers, void 0));
        constructor() {
            __runInitializers(this, _auditUpdatedAt_extraInitializers);
        }
    };
    return Agent = _classThis;
})();
export { Agent };
