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
let PromptTemplate = (() => {
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
    let _agentId_decorators;
    let _agentId_initializers = [];
    let _agentId_extraInitializers = [];
    let _name_decorators;
    let _name_initializers = [];
    let _name_extraInitializers = [];
    let _version_decorators;
    let _version_initializers = [];
    let _version_extraInitializers = [];
    let _body_decorators;
    let _body_initializers = [];
    let _body_extraInitializers = [];
    let _ownerSub_decorators;
    let _ownerSub_initializers = [];
    let _ownerSub_extraInitializers = [];
    let _auditCreatedAt_decorators;
    let _auditCreatedAt_initializers = [];
    let _auditCreatedAt_extraInitializers = [];
    var PromptTemplate = class {
        static { _classThis = this; }
        static {
            const _metadata = typeof Symbol === "function" && Symbol.metadata ? Object.create(null) : void 0;
            _id_decorators = [uuid()];
            _agentId_decorators = [text({ max: 200 })];
            _name_decorators = [text({ max: 200 })];
            _version_decorators = [int()];
            _body_decorators = [text({ max: 4000 })];
            _ownerSub_decorators = [text({ max: 200 })];
            _auditCreatedAt_decorators = [date()];
            __esDecorate(null, null, _id_decorators, { kind: "field", name: "id", static: false, private: false, access: { has: obj => "id" in obj, get: obj => obj.id, set: (obj, value) => { obj.id = value; } }, metadata: _metadata }, _id_initializers, _id_extraInitializers);
            __esDecorate(null, null, _agentId_decorators, { kind: "field", name: "agentId", static: false, private: false, access: { has: obj => "agentId" in obj, get: obj => obj.agentId, set: (obj, value) => { obj.agentId = value; } }, metadata: _metadata }, _agentId_initializers, _agentId_extraInitializers);
            __esDecorate(null, null, _name_decorators, { kind: "field", name: "name", static: false, private: false, access: { has: obj => "name" in obj, get: obj => obj.name, set: (obj, value) => { obj.name = value; } }, metadata: _metadata }, _name_initializers, _name_extraInitializers);
            __esDecorate(null, null, _version_decorators, { kind: "field", name: "version", static: false, private: false, access: { has: obj => "version" in obj, get: obj => obj.version, set: (obj, value) => { obj.version = value; } }, metadata: _metadata }, _version_initializers, _version_extraInitializers);
            __esDecorate(null, null, _body_decorators, { kind: "field", name: "body", static: false, private: false, access: { has: obj => "body" in obj, get: obj => obj.body, set: (obj, value) => { obj.body = value; } }, metadata: _metadata }, _body_initializers, _body_extraInitializers);
            __esDecorate(null, null, _ownerSub_decorators, { kind: "field", name: "ownerSub", static: false, private: false, access: { has: obj => "ownerSub" in obj, get: obj => obj.ownerSub, set: (obj, value) => { obj.ownerSub = value; } }, metadata: _metadata }, _ownerSub_initializers, _ownerSub_extraInitializers);
            __esDecorate(null, null, _auditCreatedAt_decorators, { kind: "field", name: "auditCreatedAt", static: false, private: false, access: { has: obj => "auditCreatedAt" in obj, get: obj => obj.auditCreatedAt, set: (obj, value) => { obj.auditCreatedAt = value; } }, metadata: _metadata }, _auditCreatedAt_initializers, _auditCreatedAt_extraInitializers);
            __esDecorate(null, _classDescriptor = { value: _classThis }, _classDecorators, { kind: "class", name: _classThis.name, metadata: _metadata }, null, _classExtraInitializers);
            PromptTemplate = _classThis = _classDescriptor.value;
            if (_metadata) Object.defineProperty(_classThis, Symbol.metadata, { enumerable: true, configurable: true, writable: true, value: _metadata });
            __runInitializers(_classThis, _classExtraInitializers);
        }
        id = __runInitializers(this, _id_initializers, void 0);
        agentId = (__runInitializers(this, _id_extraInitializers), __runInitializers(this, _agentId_initializers, void 0));
        name = (__runInitializers(this, _agentId_extraInitializers), __runInitializers(this, _name_initializers, void 0));
        version = (__runInitializers(this, _name_extraInitializers), __runInitializers(this, _version_initializers, void 0));
        body = (__runInitializers(this, _version_extraInitializers), __runInitializers(this, _body_initializers, void 0));
        ownerSub = (__runInitializers(this, _body_extraInitializers), __runInitializers(this, _ownerSub_initializers, void 0));
        auditCreatedAt = (__runInitializers(this, _ownerSub_extraInitializers), __runInitializers(this, _auditCreatedAt_initializers, void 0));
        constructor() {
            __runInitializers(this, _auditCreatedAt_extraInitializers);
        }
    };
    return PromptTemplate = _classThis;
})();
export { PromptTemplate };
