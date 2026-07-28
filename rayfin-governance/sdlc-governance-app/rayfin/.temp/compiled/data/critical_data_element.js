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
import { entity, uuid, text, authenticated } from '@microsoft/rayfin-core';
// Mirrors `critical_data_elements:` in
// fabric-sdlc-governance/contracts/governance/critical_data_elements.yml
let CriticalDataElement = (() => {
    let _classDecorators = [entity(), authenticated(['read']), authenticated(['create', 'update', 'delete'], {
            policy: (claims) => claims.role.eq('governance-admin').or(claims.role.eq('domain-steward')),
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
    let _domainId_decorators;
    let _domainId_initializers = [];
    let _domainId_extraInitializers = [];
    let _description_decorators;
    let _description_initializers = [];
    let _description_extraInitializers = [];
    let _dataType_decorators;
    let _dataType_initializers = [];
    let _dataType_extraInitializers = [];
    let _sensitivity_decorators;
    let _sensitivity_initializers = [];
    let _sensitivity_extraInitializers = [];
    let _columnsJson_decorators;
    let _columnsJson_initializers = [];
    let _columnsJson_extraInitializers = [];
    let _relatedTermsCsv_decorators;
    let _relatedTermsCsv_initializers = [];
    let _relatedTermsCsv_extraInitializers = [];
    let _envKey_decorators;
    let _envKey_initializers = [];
    let _envKey_extraInitializers = [];
    var CriticalDataElement = class {
        static { _classThis = this; }
        static {
            const _metadata = typeof Symbol === "function" && Symbol.metadata ? Object.create(null) : void 0;
            _id_decorators = [uuid()];
            _name_decorators = [text({ max: 200 })];
            _domainId_decorators = [text({ max: 200 })];
            _description_decorators = [text({ max: 1000 })];
            _dataType_decorators = [text({ max: 100 })];
            _sensitivity_decorators = [text({ max: 100 })];
            _columnsJson_decorators = [text({ optional: true, max: 4000 })];
            _relatedTermsCsv_decorators = [text({ optional: true, max: 4000 })];
            _envKey_decorators = [text({ max: 100 })];
            __esDecorate(null, null, _id_decorators, { kind: "field", name: "id", static: false, private: false, access: { has: obj => "id" in obj, get: obj => obj.id, set: (obj, value) => { obj.id = value; } }, metadata: _metadata }, _id_initializers, _id_extraInitializers);
            __esDecorate(null, null, _name_decorators, { kind: "field", name: "name", static: false, private: false, access: { has: obj => "name" in obj, get: obj => obj.name, set: (obj, value) => { obj.name = value; } }, metadata: _metadata }, _name_initializers, _name_extraInitializers);
            __esDecorate(null, null, _domainId_decorators, { kind: "field", name: "domainId", static: false, private: false, access: { has: obj => "domainId" in obj, get: obj => obj.domainId, set: (obj, value) => { obj.domainId = value; } }, metadata: _metadata }, _domainId_initializers, _domainId_extraInitializers);
            __esDecorate(null, null, _description_decorators, { kind: "field", name: "description", static: false, private: false, access: { has: obj => "description" in obj, get: obj => obj.description, set: (obj, value) => { obj.description = value; } }, metadata: _metadata }, _description_initializers, _description_extraInitializers);
            __esDecorate(null, null, _dataType_decorators, { kind: "field", name: "dataType", static: false, private: false, access: { has: obj => "dataType" in obj, get: obj => obj.dataType, set: (obj, value) => { obj.dataType = value; } }, metadata: _metadata }, _dataType_initializers, _dataType_extraInitializers);
            __esDecorate(null, null, _sensitivity_decorators, { kind: "field", name: "sensitivity", static: false, private: false, access: { has: obj => "sensitivity" in obj, get: obj => obj.sensitivity, set: (obj, value) => { obj.sensitivity = value; } }, metadata: _metadata }, _sensitivity_initializers, _sensitivity_extraInitializers);
            __esDecorate(null, null, _columnsJson_decorators, { kind: "field", name: "columnsJson", static: false, private: false, access: { has: obj => "columnsJson" in obj, get: obj => obj.columnsJson, set: (obj, value) => { obj.columnsJson = value; } }, metadata: _metadata }, _columnsJson_initializers, _columnsJson_extraInitializers);
            __esDecorate(null, null, _relatedTermsCsv_decorators, { kind: "field", name: "relatedTermsCsv", static: false, private: false, access: { has: obj => "relatedTermsCsv" in obj, get: obj => obj.relatedTermsCsv, set: (obj, value) => { obj.relatedTermsCsv = value; } }, metadata: _metadata }, _relatedTermsCsv_initializers, _relatedTermsCsv_extraInitializers);
            __esDecorate(null, null, _envKey_decorators, { kind: "field", name: "envKey", static: false, private: false, access: { has: obj => "envKey" in obj, get: obj => obj.envKey, set: (obj, value) => { obj.envKey = value; } }, metadata: _metadata }, _envKey_initializers, _envKey_extraInitializers);
            __esDecorate(null, _classDescriptor = { value: _classThis }, _classDecorators, { kind: "class", name: _classThis.name, metadata: _metadata }, null, _classExtraInitializers);
            CriticalDataElement = _classThis = _classDescriptor.value;
            if (_metadata) Object.defineProperty(_classThis, Symbol.metadata, { enumerable: true, configurable: true, writable: true, value: _metadata });
            __runInitializers(_classThis, _classExtraInitializers);
        }
        id = __runInitializers(this, _id_initializers, void 0);
        name = (__runInitializers(this, _id_extraInitializers), __runInitializers(this, _name_initializers, void 0));
        domainId = (__runInitializers(this, _name_extraInitializers), __runInitializers(this, _domainId_initializers, void 0));
        description = (__runInitializers(this, _domainId_extraInitializers), __runInitializers(this, _description_initializers, void 0));
        dataType = (__runInitializers(this, _description_extraInitializers), __runInitializers(this, _dataType_initializers, void 0));
        sensitivity = (__runInitializers(this, _dataType_extraInitializers), __runInitializers(this, _sensitivity_initializers, void 0));
        columnsJson = (__runInitializers(this, _sensitivity_extraInitializers), __runInitializers(this, _columnsJson_initializers, void 0));
        relatedTermsCsv = (__runInitializers(this, _columnsJson_extraInitializers), __runInitializers(this, _relatedTermsCsv_initializers, void 0));
        envKey = (__runInitializers(this, _relatedTermsCsv_extraInitializers), __runInitializers(this, _envKey_initializers, void 0));
        constructor() {
            __runInitializers(this, _envKey_extraInitializers);
        }
    };
    return CriticalDataElement = _classThis;
})();
export { CriticalDataElement };
