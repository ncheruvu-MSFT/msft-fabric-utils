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
import { entity, uuid, text, boolean, authenticated } from '@microsoft/rayfin-core';
let Workspace = (() => {
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
    let _fabricWorkspaceId_decorators;
    let _fabricWorkspaceId_initializers = [];
    let _fabricWorkspaceId_extraInitializers = [];
    let _envKey_decorators;
    let _envKey_initializers = [];
    let _envKey_extraInitializers = [];
    let _domainId_decorators;
    let _domainId_initializers = [];
    let _domainId_extraInitializers = [];
    let _isPrivateLink_decorators;
    let _isPrivateLink_initializers = [];
    let _isPrivateLink_extraInitializers = [];
    let _ownerEmail_decorators;
    let _ownerEmail_initializers = [];
    let _ownerEmail_extraInitializers = [];
    var Workspace = class {
        static { _classThis = this; }
        static {
            const _metadata = typeof Symbol === "function" && Symbol.metadata ? Object.create(null) : void 0;
            _id_decorators = [uuid()];
            _name_decorators = [text({ max: 200 })];
            _fabricWorkspaceId_decorators = [text({ max: 200 })];
            _envKey_decorators = [text({ max: 100 })];
            _domainId_decorators = [text({ max: 200 })];
            _isPrivateLink_decorators = [boolean()];
            _ownerEmail_decorators = [text({ max: 200 })];
            __esDecorate(null, null, _id_decorators, { kind: "field", name: "id", static: false, private: false, access: { has: obj => "id" in obj, get: obj => obj.id, set: (obj, value) => { obj.id = value; } }, metadata: _metadata }, _id_initializers, _id_extraInitializers);
            __esDecorate(null, null, _name_decorators, { kind: "field", name: "name", static: false, private: false, access: { has: obj => "name" in obj, get: obj => obj.name, set: (obj, value) => { obj.name = value; } }, metadata: _metadata }, _name_initializers, _name_extraInitializers);
            __esDecorate(null, null, _fabricWorkspaceId_decorators, { kind: "field", name: "fabricWorkspaceId", static: false, private: false, access: { has: obj => "fabricWorkspaceId" in obj, get: obj => obj.fabricWorkspaceId, set: (obj, value) => { obj.fabricWorkspaceId = value; } }, metadata: _metadata }, _fabricWorkspaceId_initializers, _fabricWorkspaceId_extraInitializers);
            __esDecorate(null, null, _envKey_decorators, { kind: "field", name: "envKey", static: false, private: false, access: { has: obj => "envKey" in obj, get: obj => obj.envKey, set: (obj, value) => { obj.envKey = value; } }, metadata: _metadata }, _envKey_initializers, _envKey_extraInitializers);
            __esDecorate(null, null, _domainId_decorators, { kind: "field", name: "domainId", static: false, private: false, access: { has: obj => "domainId" in obj, get: obj => obj.domainId, set: (obj, value) => { obj.domainId = value; } }, metadata: _metadata }, _domainId_initializers, _domainId_extraInitializers);
            __esDecorate(null, null, _isPrivateLink_decorators, { kind: "field", name: "isPrivateLink", static: false, private: false, access: { has: obj => "isPrivateLink" in obj, get: obj => obj.isPrivateLink, set: (obj, value) => { obj.isPrivateLink = value; } }, metadata: _metadata }, _isPrivateLink_initializers, _isPrivateLink_extraInitializers);
            __esDecorate(null, null, _ownerEmail_decorators, { kind: "field", name: "ownerEmail", static: false, private: false, access: { has: obj => "ownerEmail" in obj, get: obj => obj.ownerEmail, set: (obj, value) => { obj.ownerEmail = value; } }, metadata: _metadata }, _ownerEmail_initializers, _ownerEmail_extraInitializers);
            __esDecorate(null, _classDescriptor = { value: _classThis }, _classDecorators, { kind: "class", name: _classThis.name, metadata: _metadata }, null, _classExtraInitializers);
            Workspace = _classThis = _classDescriptor.value;
            if (_metadata) Object.defineProperty(_classThis, Symbol.metadata, { enumerable: true, configurable: true, writable: true, value: _metadata });
            __runInitializers(_classThis, _classExtraInitializers);
        }
        id = __runInitializers(this, _id_initializers, void 0);
        name = (__runInitializers(this, _id_extraInitializers), __runInitializers(this, _name_initializers, void 0));
        fabricWorkspaceId = (__runInitializers(this, _name_extraInitializers), __runInitializers(this, _fabricWorkspaceId_initializers, void 0));
        envKey = (__runInitializers(this, _fabricWorkspaceId_extraInitializers), __runInitializers(this, _envKey_initializers, void 0));
        domainId = (__runInitializers(this, _envKey_extraInitializers), __runInitializers(this, _domainId_initializers, void 0));
        isPrivateLink = (__runInitializers(this, _domainId_extraInitializers), __runInitializers(this, _isPrivateLink_initializers, void 0));
        ownerEmail = (__runInitializers(this, _isPrivateLink_extraInitializers), __runInitializers(this, _ownerEmail_initializers, void 0));
        constructor() {
            __runInitializers(this, _ownerEmail_extraInitializers);
        }
    };
    return Workspace = _classThis;
})();
export { Workspace };
