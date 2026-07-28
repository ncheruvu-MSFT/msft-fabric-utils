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
let DataAsset = (() => {
    let _classDecorators = [entity(), authenticated(['read']), authenticated(['create', 'update', 'delete'], {
            policy: (claims) => claims.role.eq('lineage-admin'),
        })];
    let _classDescriptor;
    let _classExtraInitializers = [];
    let _classThis;
    let _id_decorators;
    let _id_initializers = [];
    let _id_extraInitializers = [];
    let _qualifiedName_decorators;
    let _qualifiedName_initializers = [];
    let _qualifiedName_extraInitializers = [];
    let _assetType_decorators;
    let _assetType_initializers = [];
    let _assetType_extraInitializers = [];
    let _displayName_decorators;
    let _displayName_initializers = [];
    let _displayName_extraInitializers = [];
    let _domainId_decorators;
    let _domainId_initializers = [];
    let _domainId_extraInitializers = [];
    let _purviewGuid_decorators;
    let _purviewGuid_initializers = [];
    let _purviewGuid_extraInitializers = [];
    let _auditCreatedAt_decorators;
    let _auditCreatedAt_initializers = [];
    let _auditCreatedAt_extraInitializers = [];
    let _auditUpdatedAt_decorators;
    let _auditUpdatedAt_initializers = [];
    let _auditUpdatedAt_extraInitializers = [];
    var DataAsset = class {
        static { _classThis = this; }
        static {
            const _metadata = typeof Symbol === "function" && Symbol.metadata ? Object.create(null) : void 0;
            _id_decorators = [uuid()];
            _qualifiedName_decorators = [text({ max: 400 })];
            _assetType_decorators = [text({ max: 100 })];
            _displayName_decorators = [text({ max: 200 })];
            _domainId_decorators = [text({ optional: true, max: 200 })];
            _purviewGuid_decorators = [text({ optional: true, max: 200 })];
            _auditCreatedAt_decorators = [date()];
            _auditUpdatedAt_decorators = [date({ optional: true })];
            __esDecorate(null, null, _id_decorators, { kind: "field", name: "id", static: false, private: false, access: { has: obj => "id" in obj, get: obj => obj.id, set: (obj, value) => { obj.id = value; } }, metadata: _metadata }, _id_initializers, _id_extraInitializers);
            __esDecorate(null, null, _qualifiedName_decorators, { kind: "field", name: "qualifiedName", static: false, private: false, access: { has: obj => "qualifiedName" in obj, get: obj => obj.qualifiedName, set: (obj, value) => { obj.qualifiedName = value; } }, metadata: _metadata }, _qualifiedName_initializers, _qualifiedName_extraInitializers);
            __esDecorate(null, null, _assetType_decorators, { kind: "field", name: "assetType", static: false, private: false, access: { has: obj => "assetType" in obj, get: obj => obj.assetType, set: (obj, value) => { obj.assetType = value; } }, metadata: _metadata }, _assetType_initializers, _assetType_extraInitializers);
            __esDecorate(null, null, _displayName_decorators, { kind: "field", name: "displayName", static: false, private: false, access: { has: obj => "displayName" in obj, get: obj => obj.displayName, set: (obj, value) => { obj.displayName = value; } }, metadata: _metadata }, _displayName_initializers, _displayName_extraInitializers);
            __esDecorate(null, null, _domainId_decorators, { kind: "field", name: "domainId", static: false, private: false, access: { has: obj => "domainId" in obj, get: obj => obj.domainId, set: (obj, value) => { obj.domainId = value; } }, metadata: _metadata }, _domainId_initializers, _domainId_extraInitializers);
            __esDecorate(null, null, _purviewGuid_decorators, { kind: "field", name: "purviewGuid", static: false, private: false, access: { has: obj => "purviewGuid" in obj, get: obj => obj.purviewGuid, set: (obj, value) => { obj.purviewGuid = value; } }, metadata: _metadata }, _purviewGuid_initializers, _purviewGuid_extraInitializers);
            __esDecorate(null, null, _auditCreatedAt_decorators, { kind: "field", name: "auditCreatedAt", static: false, private: false, access: { has: obj => "auditCreatedAt" in obj, get: obj => obj.auditCreatedAt, set: (obj, value) => { obj.auditCreatedAt = value; } }, metadata: _metadata }, _auditCreatedAt_initializers, _auditCreatedAt_extraInitializers);
            __esDecorate(null, null, _auditUpdatedAt_decorators, { kind: "field", name: "auditUpdatedAt", static: false, private: false, access: { has: obj => "auditUpdatedAt" in obj, get: obj => obj.auditUpdatedAt, set: (obj, value) => { obj.auditUpdatedAt = value; } }, metadata: _metadata }, _auditUpdatedAt_initializers, _auditUpdatedAt_extraInitializers);
            __esDecorate(null, _classDescriptor = { value: _classThis }, _classDecorators, { kind: "class", name: _classThis.name, metadata: _metadata }, null, _classExtraInitializers);
            DataAsset = _classThis = _classDescriptor.value;
            if (_metadata) Object.defineProperty(_classThis, Symbol.metadata, { enumerable: true, configurable: true, writable: true, value: _metadata });
            __runInitializers(_classThis, _classExtraInitializers);
        }
        id = __runInitializers(this, _id_initializers, void 0);
        qualifiedName = (__runInitializers(this, _id_extraInitializers), __runInitializers(this, _qualifiedName_initializers, void 0));
        assetType = (__runInitializers(this, _qualifiedName_extraInitializers), __runInitializers(this, _assetType_initializers, void 0));
        displayName = (__runInitializers(this, _assetType_extraInitializers), __runInitializers(this, _displayName_initializers, void 0));
        domainId = (__runInitializers(this, _displayName_extraInitializers), __runInitializers(this, _domainId_initializers, void 0));
        purviewGuid = (__runInitializers(this, _domainId_extraInitializers), __runInitializers(this, _purviewGuid_initializers, void 0));
        auditCreatedAt = (__runInitializers(this, _purviewGuid_extraInitializers), __runInitializers(this, _auditCreatedAt_initializers, void 0));
        auditUpdatedAt = (__runInitializers(this, _auditCreatedAt_extraInitializers), __runInitializers(this, _auditUpdatedAt_initializers, void 0));
        constructor() {
            __runInitializers(this, _auditUpdatedAt_extraInitializers);
        }
    };
    return DataAsset = _classThis;
})();
export { DataAsset };
