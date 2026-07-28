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
let Tool = (() => {
    let _classDecorators = [entity(), authenticated(['read']), authenticated(['create', 'update', 'delete'], {
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
    let _kind_decorators;
    let _kind_initializers = [];
    let _kind_extraInitializers = [];
    let _endpoint_decorators;
    let _endpoint_initializers = [];
    let _endpoint_extraInitializers = [];
    let _authMode_decorators;
    let _authMode_initializers = [];
    let _authMode_extraInitializers = [];
    let _isSensitive_decorators;
    let _isSensitive_initializers = [];
    let _isSensitive_extraInitializers = [];
    let _allowedDomainsCsv_decorators;
    let _allowedDomainsCsv_initializers = [];
    let _allowedDomainsCsv_extraInitializers = [];
    var Tool = class {
        static { _classThis = this; }
        static {
            const _metadata = typeof Symbol === "function" && Symbol.metadata ? Object.create(null) : void 0;
            _id_decorators = [uuid()];
            _name_decorators = [text({ max: 200 })];
            _kind_decorators = [text({ max: 100 })];
            _endpoint_decorators = [text({ max: 400 })];
            _authMode_decorators = [text({ max: 100 })];
            _isSensitive_decorators = [boolean()];
            _allowedDomainsCsv_decorators = [text({ optional: true, max: 4000 })];
            __esDecorate(null, null, _id_decorators, { kind: "field", name: "id", static: false, private: false, access: { has: obj => "id" in obj, get: obj => obj.id, set: (obj, value) => { obj.id = value; } }, metadata: _metadata }, _id_initializers, _id_extraInitializers);
            __esDecorate(null, null, _name_decorators, { kind: "field", name: "name", static: false, private: false, access: { has: obj => "name" in obj, get: obj => obj.name, set: (obj, value) => { obj.name = value; } }, metadata: _metadata }, _name_initializers, _name_extraInitializers);
            __esDecorate(null, null, _kind_decorators, { kind: "field", name: "kind", static: false, private: false, access: { has: obj => "kind" in obj, get: obj => obj.kind, set: (obj, value) => { obj.kind = value; } }, metadata: _metadata }, _kind_initializers, _kind_extraInitializers);
            __esDecorate(null, null, _endpoint_decorators, { kind: "field", name: "endpoint", static: false, private: false, access: { has: obj => "endpoint" in obj, get: obj => obj.endpoint, set: (obj, value) => { obj.endpoint = value; } }, metadata: _metadata }, _endpoint_initializers, _endpoint_extraInitializers);
            __esDecorate(null, null, _authMode_decorators, { kind: "field", name: "authMode", static: false, private: false, access: { has: obj => "authMode" in obj, get: obj => obj.authMode, set: (obj, value) => { obj.authMode = value; } }, metadata: _metadata }, _authMode_initializers, _authMode_extraInitializers);
            __esDecorate(null, null, _isSensitive_decorators, { kind: "field", name: "isSensitive", static: false, private: false, access: { has: obj => "isSensitive" in obj, get: obj => obj.isSensitive, set: (obj, value) => { obj.isSensitive = value; } }, metadata: _metadata }, _isSensitive_initializers, _isSensitive_extraInitializers);
            __esDecorate(null, null, _allowedDomainsCsv_decorators, { kind: "field", name: "allowedDomainsCsv", static: false, private: false, access: { has: obj => "allowedDomainsCsv" in obj, get: obj => obj.allowedDomainsCsv, set: (obj, value) => { obj.allowedDomainsCsv = value; } }, metadata: _metadata }, _allowedDomainsCsv_initializers, _allowedDomainsCsv_extraInitializers);
            __esDecorate(null, _classDescriptor = { value: _classThis }, _classDecorators, { kind: "class", name: _classThis.name, metadata: _metadata }, null, _classExtraInitializers);
            Tool = _classThis = _classDescriptor.value;
            if (_metadata) Object.defineProperty(_classThis, Symbol.metadata, { enumerable: true, configurable: true, writable: true, value: _metadata });
            __runInitializers(_classThis, _classExtraInitializers);
        }
        id = __runInitializers(this, _id_initializers, void 0);
        name = (__runInitializers(this, _id_extraInitializers), __runInitializers(this, _name_initializers, void 0));
        kind = (__runInitializers(this, _name_extraInitializers), __runInitializers(this, _kind_initializers, void 0));
        endpoint = (__runInitializers(this, _kind_extraInitializers), __runInitializers(this, _endpoint_initializers, void 0));
        authMode = (__runInitializers(this, _endpoint_extraInitializers), __runInitializers(this, _authMode_initializers, void 0));
        isSensitive = (__runInitializers(this, _authMode_extraInitializers), __runInitializers(this, _isSensitive_initializers, void 0));
        allowedDomainsCsv = (__runInitializers(this, _isSensitive_extraInitializers), __runInitializers(this, _allowedDomainsCsv_initializers, void 0));
        constructor() {
            __runInitializers(this, _allowedDomainsCsv_extraInitializers);
        }
    };
    return Tool = _classThis;
})();
export { Tool };
