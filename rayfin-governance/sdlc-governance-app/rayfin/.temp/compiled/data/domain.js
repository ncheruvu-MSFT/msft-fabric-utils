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
// Mirrors the `domains:` block in
// fabric-sdlc-governance/contracts/governance/domains.yml
let Domain = (() => {
    let _classDecorators = [entity(), authenticated(['read']), authenticated(['create', 'update', 'delete'], {
            policy: (claims) => claims.role.eq('governance-admin'),
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
    let _type_decorators;
    let _type_initializers = [];
    let _type_extraInitializers = [];
    let _envKey_decorators;
    let _envKey_initializers = [];
    let _envKey_extraInitializers = [];
    let _status_decorators;
    let _status_initializers = [];
    let _status_extraInitializers = [];
    let _parentId_decorators;
    let _parentId_initializers = [];
    let _parentId_extraInitializers = [];
    let _fabricWorkspace_decorators;
    let _fabricWorkspace_initializers = [];
    let _fabricWorkspace_extraInitializers = [];
    let _purviewCollection_decorators;
    let _purviewCollection_initializers = [];
    let _purviewCollection_extraInitializers = [];
    let _ownerEmail_decorators;
    let _ownerEmail_initializers = [];
    let _ownerEmail_extraInitializers = [];
    let _isActive_decorators;
    let _isActive_initializers = [];
    let _isActive_extraInitializers = [];
    let _auditCreatedAt_decorators;
    let _auditCreatedAt_initializers = [];
    let _auditCreatedAt_extraInitializers = [];
    let _auditUpdatedAt_decorators;
    let _auditUpdatedAt_initializers = [];
    let _auditUpdatedAt_extraInitializers = [];
    var Domain = class {
        static { _classThis = this; }
        static {
            const _metadata = typeof Symbol === "function" && Symbol.metadata ? Object.create(null) : void 0;
            _id_decorators = [uuid()];
            _name_decorators = [text({ max: 200 })];
            _description_decorators = [text({ optional: true, max: 1000 })];
            _type_decorators = [text({ max: 100 })];
            _envKey_decorators = [text({ max: 100 })];
            _status_decorators = [text({ max: 100 })];
            _parentId_decorators = [text({ optional: true, max: 200 })];
            _fabricWorkspace_decorators = [text({ optional: true, max: 200 })];
            _purviewCollection_decorators = [text({ optional: true, max: 200 })];
            _ownerEmail_decorators = [text({ max: 200 })];
            _isActive_decorators = [boolean()];
            _auditCreatedAt_decorators = [date()];
            _auditUpdatedAt_decorators = [date({ optional: true })];
            __esDecorate(null, null, _id_decorators, { kind: "field", name: "id", static: false, private: false, access: { has: obj => "id" in obj, get: obj => obj.id, set: (obj, value) => { obj.id = value; } }, metadata: _metadata }, _id_initializers, _id_extraInitializers);
            __esDecorate(null, null, _name_decorators, { kind: "field", name: "name", static: false, private: false, access: { has: obj => "name" in obj, get: obj => obj.name, set: (obj, value) => { obj.name = value; } }, metadata: _metadata }, _name_initializers, _name_extraInitializers);
            __esDecorate(null, null, _description_decorators, { kind: "field", name: "description", static: false, private: false, access: { has: obj => "description" in obj, get: obj => obj.description, set: (obj, value) => { obj.description = value; } }, metadata: _metadata }, _description_initializers, _description_extraInitializers);
            __esDecorate(null, null, _type_decorators, { kind: "field", name: "type", static: false, private: false, access: { has: obj => "type" in obj, get: obj => obj.type, set: (obj, value) => { obj.type = value; } }, metadata: _metadata }, _type_initializers, _type_extraInitializers);
            __esDecorate(null, null, _envKey_decorators, { kind: "field", name: "envKey", static: false, private: false, access: { has: obj => "envKey" in obj, get: obj => obj.envKey, set: (obj, value) => { obj.envKey = value; } }, metadata: _metadata }, _envKey_initializers, _envKey_extraInitializers);
            __esDecorate(null, null, _status_decorators, { kind: "field", name: "status", static: false, private: false, access: { has: obj => "status" in obj, get: obj => obj.status, set: (obj, value) => { obj.status = value; } }, metadata: _metadata }, _status_initializers, _status_extraInitializers);
            __esDecorate(null, null, _parentId_decorators, { kind: "field", name: "parentId", static: false, private: false, access: { has: obj => "parentId" in obj, get: obj => obj.parentId, set: (obj, value) => { obj.parentId = value; } }, metadata: _metadata }, _parentId_initializers, _parentId_extraInitializers);
            __esDecorate(null, null, _fabricWorkspace_decorators, { kind: "field", name: "fabricWorkspace", static: false, private: false, access: { has: obj => "fabricWorkspace" in obj, get: obj => obj.fabricWorkspace, set: (obj, value) => { obj.fabricWorkspace = value; } }, metadata: _metadata }, _fabricWorkspace_initializers, _fabricWorkspace_extraInitializers);
            __esDecorate(null, null, _purviewCollection_decorators, { kind: "field", name: "purviewCollection", static: false, private: false, access: { has: obj => "purviewCollection" in obj, get: obj => obj.purviewCollection, set: (obj, value) => { obj.purviewCollection = value; } }, metadata: _metadata }, _purviewCollection_initializers, _purviewCollection_extraInitializers);
            __esDecorate(null, null, _ownerEmail_decorators, { kind: "field", name: "ownerEmail", static: false, private: false, access: { has: obj => "ownerEmail" in obj, get: obj => obj.ownerEmail, set: (obj, value) => { obj.ownerEmail = value; } }, metadata: _metadata }, _ownerEmail_initializers, _ownerEmail_extraInitializers);
            __esDecorate(null, null, _isActive_decorators, { kind: "field", name: "isActive", static: false, private: false, access: { has: obj => "isActive" in obj, get: obj => obj.isActive, set: (obj, value) => { obj.isActive = value; } }, metadata: _metadata }, _isActive_initializers, _isActive_extraInitializers);
            __esDecorate(null, null, _auditCreatedAt_decorators, { kind: "field", name: "auditCreatedAt", static: false, private: false, access: { has: obj => "auditCreatedAt" in obj, get: obj => obj.auditCreatedAt, set: (obj, value) => { obj.auditCreatedAt = value; } }, metadata: _metadata }, _auditCreatedAt_initializers, _auditCreatedAt_extraInitializers);
            __esDecorate(null, null, _auditUpdatedAt_decorators, { kind: "field", name: "auditUpdatedAt", static: false, private: false, access: { has: obj => "auditUpdatedAt" in obj, get: obj => obj.auditUpdatedAt, set: (obj, value) => { obj.auditUpdatedAt = value; } }, metadata: _metadata }, _auditUpdatedAt_initializers, _auditUpdatedAt_extraInitializers);
            __esDecorate(null, _classDescriptor = { value: _classThis }, _classDecorators, { kind: "class", name: _classThis.name, metadata: _metadata }, null, _classExtraInitializers);
            Domain = _classThis = _classDescriptor.value;
            if (_metadata) Object.defineProperty(_classThis, Symbol.metadata, { enumerable: true, configurable: true, writable: true, value: _metadata });
            __runInitializers(_classThis, _classExtraInitializers);
        }
        id = __runInitializers(this, _id_initializers, void 0);
        name = (__runInitializers(this, _id_extraInitializers), __runInitializers(this, _name_initializers, void 0));
        description = (__runInitializers(this, _name_extraInitializers), __runInitializers(this, _description_initializers, void 0));
        type = (__runInitializers(this, _description_extraInitializers), __runInitializers(this, _type_initializers, void 0));
        envKey = (__runInitializers(this, _type_extraInitializers), __runInitializers(this, _envKey_initializers, void 0));
        status = (__runInitializers(this, _envKey_extraInitializers), __runInitializers(this, _status_initializers, void 0));
        parentId = (__runInitializers(this, _status_extraInitializers), __runInitializers(this, _parentId_initializers, void 0));
        fabricWorkspace = (__runInitializers(this, _parentId_extraInitializers), __runInitializers(this, _fabricWorkspace_initializers, void 0));
        purviewCollection = (__runInitializers(this, _fabricWorkspace_extraInitializers), __runInitializers(this, _purviewCollection_initializers, void 0));
        ownerEmail = (__runInitializers(this, _purviewCollection_extraInitializers), __runInitializers(this, _ownerEmail_initializers, void 0));
        isActive = (__runInitializers(this, _ownerEmail_extraInitializers), __runInitializers(this, _isActive_initializers, void 0));
        auditCreatedAt = (__runInitializers(this, _isActive_extraInitializers), __runInitializers(this, _auditCreatedAt_initializers, void 0));
        auditUpdatedAt = (__runInitializers(this, _auditCreatedAt_extraInitializers), __runInitializers(this, _auditUpdatedAt_initializers, void 0));
        constructor() {
            __runInitializers(this, _auditUpdatedAt_extraInitializers);
        }
    };
    return Domain = _classThis;
})();
export { Domain };
