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
let LineageEdge = (() => {
    let _classDecorators = [entity(), authenticated(['read']), authenticated(['create']), authenticated(['update', 'delete'], {
            policy: (claims, item) => claims.role.eq('lineage-admin').or(claims.sub.eq(item.harvestedBySub)),
        })];
    let _classDescriptor;
    let _classExtraInitializers = [];
    let _classThis;
    let _id_decorators;
    let _id_initializers = [];
    let _id_extraInitializers = [];
    let _sourceQname_decorators;
    let _sourceQname_initializers = [];
    let _sourceQname_extraInitializers = [];
    let _sourceType_decorators;
    let _sourceType_initializers = [];
    let _sourceType_extraInitializers = [];
    let _targetQname_decorators;
    let _targetQname_initializers = [];
    let _targetQname_extraInitializers = [];
    let _targetType_decorators;
    let _targetType_initializers = [];
    let _targetType_extraInitializers = [];
    let _processName_decorators;
    let _processName_initializers = [];
    let _processName_extraInitializers = [];
    let _processType_decorators;
    let _processType_initializers = [];
    let _processType_extraInitializers = [];
    let _artifactRef_decorators;
    let _artifactRef_initializers = [];
    let _artifactRef_extraInitializers = [];
    let _harvestedBySub_decorators;
    let _harvestedBySub_initializers = [];
    let _harvestedBySub_extraInitializers = [];
    let _columnsJson_decorators;
    let _columnsJson_initializers = [];
    let _columnsJson_extraInitializers = [];
    let _extraJson_decorators;
    let _extraJson_initializers = [];
    let _extraJson_extraInitializers = [];
    let _harvestedAt_decorators;
    let _harvestedAt_initializers = [];
    let _harvestedAt_extraInitializers = [];
    var LineageEdge = class {
        static { _classThis = this; }
        static {
            const _metadata = typeof Symbol === "function" && Symbol.metadata ? Object.create(null) : void 0;
            _id_decorators = [uuid()];
            _sourceQname_decorators = [text({ max: 400 })];
            _sourceType_decorators = [text({ max: 100 })];
            _targetQname_decorators = [text({ max: 400 })];
            _targetType_decorators = [text({ max: 100 })];
            _processName_decorators = [text({ max: 200 })];
            _processType_decorators = [text({ max: 100 })];
            _artifactRef_decorators = [text({ max: 400 })];
            _harvestedBySub_decorators = [text({ max: 200 })];
            _columnsJson_decorators = [text({ optional: true, max: 4000 })];
            _extraJson_decorators = [text({ optional: true, max: 4000 })];
            _harvestedAt_decorators = [date()];
            __esDecorate(null, null, _id_decorators, { kind: "field", name: "id", static: false, private: false, access: { has: obj => "id" in obj, get: obj => obj.id, set: (obj, value) => { obj.id = value; } }, metadata: _metadata }, _id_initializers, _id_extraInitializers);
            __esDecorate(null, null, _sourceQname_decorators, { kind: "field", name: "sourceQname", static: false, private: false, access: { has: obj => "sourceQname" in obj, get: obj => obj.sourceQname, set: (obj, value) => { obj.sourceQname = value; } }, metadata: _metadata }, _sourceQname_initializers, _sourceQname_extraInitializers);
            __esDecorate(null, null, _sourceType_decorators, { kind: "field", name: "sourceType", static: false, private: false, access: { has: obj => "sourceType" in obj, get: obj => obj.sourceType, set: (obj, value) => { obj.sourceType = value; } }, metadata: _metadata }, _sourceType_initializers, _sourceType_extraInitializers);
            __esDecorate(null, null, _targetQname_decorators, { kind: "field", name: "targetQname", static: false, private: false, access: { has: obj => "targetQname" in obj, get: obj => obj.targetQname, set: (obj, value) => { obj.targetQname = value; } }, metadata: _metadata }, _targetQname_initializers, _targetQname_extraInitializers);
            __esDecorate(null, null, _targetType_decorators, { kind: "field", name: "targetType", static: false, private: false, access: { has: obj => "targetType" in obj, get: obj => obj.targetType, set: (obj, value) => { obj.targetType = value; } }, metadata: _metadata }, _targetType_initializers, _targetType_extraInitializers);
            __esDecorate(null, null, _processName_decorators, { kind: "field", name: "processName", static: false, private: false, access: { has: obj => "processName" in obj, get: obj => obj.processName, set: (obj, value) => { obj.processName = value; } }, metadata: _metadata }, _processName_initializers, _processName_extraInitializers);
            __esDecorate(null, null, _processType_decorators, { kind: "field", name: "processType", static: false, private: false, access: { has: obj => "processType" in obj, get: obj => obj.processType, set: (obj, value) => { obj.processType = value; } }, metadata: _metadata }, _processType_initializers, _processType_extraInitializers);
            __esDecorate(null, null, _artifactRef_decorators, { kind: "field", name: "artifactRef", static: false, private: false, access: { has: obj => "artifactRef" in obj, get: obj => obj.artifactRef, set: (obj, value) => { obj.artifactRef = value; } }, metadata: _metadata }, _artifactRef_initializers, _artifactRef_extraInitializers);
            __esDecorate(null, null, _harvestedBySub_decorators, { kind: "field", name: "harvestedBySub", static: false, private: false, access: { has: obj => "harvestedBySub" in obj, get: obj => obj.harvestedBySub, set: (obj, value) => { obj.harvestedBySub = value; } }, metadata: _metadata }, _harvestedBySub_initializers, _harvestedBySub_extraInitializers);
            __esDecorate(null, null, _columnsJson_decorators, { kind: "field", name: "columnsJson", static: false, private: false, access: { has: obj => "columnsJson" in obj, get: obj => obj.columnsJson, set: (obj, value) => { obj.columnsJson = value; } }, metadata: _metadata }, _columnsJson_initializers, _columnsJson_extraInitializers);
            __esDecorate(null, null, _extraJson_decorators, { kind: "field", name: "extraJson", static: false, private: false, access: { has: obj => "extraJson" in obj, get: obj => obj.extraJson, set: (obj, value) => { obj.extraJson = value; } }, metadata: _metadata }, _extraJson_initializers, _extraJson_extraInitializers);
            __esDecorate(null, null, _harvestedAt_decorators, { kind: "field", name: "harvestedAt", static: false, private: false, access: { has: obj => "harvestedAt" in obj, get: obj => obj.harvestedAt, set: (obj, value) => { obj.harvestedAt = value; } }, metadata: _metadata }, _harvestedAt_initializers, _harvestedAt_extraInitializers);
            __esDecorate(null, _classDescriptor = { value: _classThis }, _classDecorators, { kind: "class", name: _classThis.name, metadata: _metadata }, null, _classExtraInitializers);
            LineageEdge = _classThis = _classDescriptor.value;
            if (_metadata) Object.defineProperty(_classThis, Symbol.metadata, { enumerable: true, configurable: true, writable: true, value: _metadata });
            __runInitializers(_classThis, _classExtraInitializers);
        }
        id = __runInitializers(this, _id_initializers, void 0);
        sourceQname = (__runInitializers(this, _id_extraInitializers), __runInitializers(this, _sourceQname_initializers, void 0));
        sourceType = (__runInitializers(this, _sourceQname_extraInitializers), __runInitializers(this, _sourceType_initializers, void 0));
        targetQname = (__runInitializers(this, _sourceType_extraInitializers), __runInitializers(this, _targetQname_initializers, void 0));
        targetType = (__runInitializers(this, _targetQname_extraInitializers), __runInitializers(this, _targetType_initializers, void 0));
        processName = (__runInitializers(this, _targetType_extraInitializers), __runInitializers(this, _processName_initializers, void 0));
        processType = (__runInitializers(this, _processName_extraInitializers), __runInitializers(this, _processType_initializers, void 0));
        artifactRef = (__runInitializers(this, _processType_extraInitializers), __runInitializers(this, _artifactRef_initializers, void 0));
        harvestedBySub = (__runInitializers(this, _artifactRef_extraInitializers), __runInitializers(this, _harvestedBySub_initializers, void 0));
        columnsJson = (__runInitializers(this, _harvestedBySub_extraInitializers), __runInitializers(this, _columnsJson_initializers, void 0));
        extraJson = (__runInitializers(this, _columnsJson_extraInitializers), __runInitializers(this, _extraJson_initializers, void 0));
        harvestedAt = (__runInitializers(this, _extraJson_extraInitializers), __runInitializers(this, _harvestedAt_initializers, void 0));
        constructor() {
            __runInitializers(this, _harvestedAt_extraInitializers);
        }
    };
    return LineageEdge = _classThis;
})();
export { LineageEdge };
