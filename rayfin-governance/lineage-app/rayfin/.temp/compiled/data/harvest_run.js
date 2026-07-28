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
let HarvestRun = (() => {
    let _classDecorators = [entity(), authenticated(['read']), authenticated(['create']), authenticated(['update', 'delete'], {
            policy: (claims, item) => claims.role.eq('lineage-admin').or(claims.sub.eq(item.triggeredBySub)),
        })];
    let _classDescriptor;
    let _classExtraInitializers = [];
    let _classThis;
    let _id_decorators;
    let _id_initializers = [];
    let _id_extraInitializers = [];
    let _harvesterType_decorators;
    let _harvesterType_initializers = [];
    let _harvesterType_extraInitializers = [];
    let _status_decorators;
    let _status_initializers = [];
    let _status_extraInitializers = [];
    let _edgeCount_decorators;
    let _edgeCount_initializers = [];
    let _edgeCount_extraInitializers = [];
    let _triggeredBySub_decorators;
    let _triggeredBySub_initializers = [];
    let _triggeredBySub_extraInitializers = [];
    let _errorMessage_decorators;
    let _errorMessage_initializers = [];
    let _errorMessage_extraInitializers = [];
    let _startedAt_decorators;
    let _startedAt_initializers = [];
    let _startedAt_extraInitializers = [];
    let _finishedAt_decorators;
    let _finishedAt_initializers = [];
    let _finishedAt_extraInitializers = [];
    var HarvestRun = class {
        static { _classThis = this; }
        static {
            const _metadata = typeof Symbol === "function" && Symbol.metadata ? Object.create(null) : void 0;
            _id_decorators = [uuid()];
            _harvesterType_decorators = [text({ max: 100 })];
            _status_decorators = [text({ max: 100 })];
            _edgeCount_decorators = [int()];
            _triggeredBySub_decorators = [text({ max: 200 })];
            _errorMessage_decorators = [text({ optional: true, max: 4000 })];
            _startedAt_decorators = [date()];
            _finishedAt_decorators = [date({ optional: true })];
            __esDecorate(null, null, _id_decorators, { kind: "field", name: "id", static: false, private: false, access: { has: obj => "id" in obj, get: obj => obj.id, set: (obj, value) => { obj.id = value; } }, metadata: _metadata }, _id_initializers, _id_extraInitializers);
            __esDecorate(null, null, _harvesterType_decorators, { kind: "field", name: "harvesterType", static: false, private: false, access: { has: obj => "harvesterType" in obj, get: obj => obj.harvesterType, set: (obj, value) => { obj.harvesterType = value; } }, metadata: _metadata }, _harvesterType_initializers, _harvesterType_extraInitializers);
            __esDecorate(null, null, _status_decorators, { kind: "field", name: "status", static: false, private: false, access: { has: obj => "status" in obj, get: obj => obj.status, set: (obj, value) => { obj.status = value; } }, metadata: _metadata }, _status_initializers, _status_extraInitializers);
            __esDecorate(null, null, _edgeCount_decorators, { kind: "field", name: "edgeCount", static: false, private: false, access: { has: obj => "edgeCount" in obj, get: obj => obj.edgeCount, set: (obj, value) => { obj.edgeCount = value; } }, metadata: _metadata }, _edgeCount_initializers, _edgeCount_extraInitializers);
            __esDecorate(null, null, _triggeredBySub_decorators, { kind: "field", name: "triggeredBySub", static: false, private: false, access: { has: obj => "triggeredBySub" in obj, get: obj => obj.triggeredBySub, set: (obj, value) => { obj.triggeredBySub = value; } }, metadata: _metadata }, _triggeredBySub_initializers, _triggeredBySub_extraInitializers);
            __esDecorate(null, null, _errorMessage_decorators, { kind: "field", name: "errorMessage", static: false, private: false, access: { has: obj => "errorMessage" in obj, get: obj => obj.errorMessage, set: (obj, value) => { obj.errorMessage = value; } }, metadata: _metadata }, _errorMessage_initializers, _errorMessage_extraInitializers);
            __esDecorate(null, null, _startedAt_decorators, { kind: "field", name: "startedAt", static: false, private: false, access: { has: obj => "startedAt" in obj, get: obj => obj.startedAt, set: (obj, value) => { obj.startedAt = value; } }, metadata: _metadata }, _startedAt_initializers, _startedAt_extraInitializers);
            __esDecorate(null, null, _finishedAt_decorators, { kind: "field", name: "finishedAt", static: false, private: false, access: { has: obj => "finishedAt" in obj, get: obj => obj.finishedAt, set: (obj, value) => { obj.finishedAt = value; } }, metadata: _metadata }, _finishedAt_initializers, _finishedAt_extraInitializers);
            __esDecorate(null, _classDescriptor = { value: _classThis }, _classDecorators, { kind: "class", name: _classThis.name, metadata: _metadata }, null, _classExtraInitializers);
            HarvestRun = _classThis = _classDescriptor.value;
            if (_metadata) Object.defineProperty(_classThis, Symbol.metadata, { enumerable: true, configurable: true, writable: true, value: _metadata });
            __runInitializers(_classThis, _classExtraInitializers);
        }
        id = __runInitializers(this, _id_initializers, void 0);
        harvesterType = (__runInitializers(this, _id_extraInitializers), __runInitializers(this, _harvesterType_initializers, void 0));
        status = (__runInitializers(this, _harvesterType_extraInitializers), __runInitializers(this, _status_initializers, void 0));
        edgeCount = (__runInitializers(this, _status_extraInitializers), __runInitializers(this, _edgeCount_initializers, void 0));
        triggeredBySub = (__runInitializers(this, _edgeCount_extraInitializers), __runInitializers(this, _triggeredBySub_initializers, void 0));
        errorMessage = (__runInitializers(this, _triggeredBySub_extraInitializers), __runInitializers(this, _errorMessage_initializers, void 0));
        startedAt = (__runInitializers(this, _errorMessage_extraInitializers), __runInitializers(this, _startedAt_initializers, void 0));
        finishedAt = (__runInitializers(this, _startedAt_extraInitializers), __runInitializers(this, _finishedAt_initializers, void 0));
        constructor() {
            __runInitializers(this, _finishedAt_extraInitializers);
        }
    };
    return HarvestRun = _classThis;
})();
export { HarvestRun };
