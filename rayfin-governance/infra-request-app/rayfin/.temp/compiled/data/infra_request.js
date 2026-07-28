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
// One row per infrastructure request raised from the frontend form.
//
// Lifecycle: Pending -> Approved | Rejected -> Submitted (GitHub issue opened
// by the provisioning workflow) -> Completed (platform team closes the loop).
//
// The static frontend only ever CREATES requests and (for approvers) flips the
// status to Approved/Rejected. The GitHub Actions workflow authenticates as the
// `pipeline` role to stamp `githubIssueUrl` / `githubIssueNumber` / Submitted.
let InfraRequest = (() => {
    let _classDecorators = [entity(), authenticated(['read']), authenticated(['create']), authenticated(['update'], {
            // Approvers/admins drive the approval gate; the automation role stamps the
            // GitHub fields; owners may still edit their own request while it is pending.
            policy: (claims, item) => claims.role
                .eq('infra-approver')
                .or(claims.role.eq('governance-admin'))
                .or(claims.role.eq('pipeline'))
                .or(claims.sub.eq(item.ownerSub)),
        }), authenticated(['delete'], {
            policy: (claims) => claims.role.eq('governance-admin'),
        })];
    let _classDescriptor;
    let _classExtraInitializers = [];
    let _classThis;
    let _id_decorators;
    let _id_initializers = [];
    let _id_extraInitializers = [];
    let _requestType_decorators;
    let _requestType_initializers = [];
    let _requestType_extraInitializers = [];
    let _displayName_decorators;
    let _displayName_initializers = [];
    let _displayName_extraInitializers = [];
    let _environment_decorators;
    let _environment_initializers = [];
    let _environment_extraInitializers = [];
    let _domain_decorators;
    let _domain_initializers = [];
    let _domain_extraInitializers = [];
    let _capacitySku_decorators;
    let _capacitySku_initializers = [];
    let _capacitySku_extraInitializers = [];
    let _region_decorators;
    let _region_initializers = [];
    let _region_extraInitializers = [];
    let _targetCapacity_decorators;
    let _targetCapacity_initializers = [];
    let _targetCapacity_extraInitializers = [];
    let _justification_decorators;
    let _justification_initializers = [];
    let _justification_extraInitializers = [];
    let _costCenter_decorators;
    let _costCenter_initializers = [];
    let _costCenter_extraInitializers = [];
    let _status_decorators;
    let _status_initializers = [];
    let _status_extraInitializers = [];
    let _approverSub_decorators;
    let _approverSub_initializers = [];
    let _approverSub_extraInitializers = [];
    let _approvalNote_decorators;
    let _approvalNote_initializers = [];
    let _approvalNote_extraInitializers = [];
    let _githubIssueUrl_decorators;
    let _githubIssueUrl_initializers = [];
    let _githubIssueUrl_extraInitializers = [];
    let _githubIssueNumber_decorators;
    let _githubIssueNumber_initializers = [];
    let _githubIssueNumber_extraInitializers = [];
    let _ownerSub_decorators;
    let _ownerSub_initializers = [];
    let _ownerSub_extraInitializers = [];
    let _auditCreatedBy_decorators;
    let _auditCreatedBy_initializers = [];
    let _auditCreatedBy_extraInitializers = [];
    let _auditCreatedAt_decorators;
    let _auditCreatedAt_initializers = [];
    let _auditCreatedAt_extraInitializers = [];
    let _auditUpdatedAt_decorators;
    let _auditUpdatedAt_initializers = [];
    let _auditUpdatedAt_extraInitializers = [];
    var InfraRequest = class {
        static { _classThis = this; }
        static {
            const _metadata = typeof Symbol === "function" && Symbol.metadata ? Object.create(null) : void 0;
            _id_decorators = [uuid()];
            _requestType_decorators = [text({ max: 40 })];
            _displayName_decorators = [text({ max: 200 })];
            _environment_decorators = [text({ max: 40 })];
            _domain_decorators = [text({ optional: true, max: 200 })];
            _capacitySku_decorators = [text({ optional: true, max: 40 })];
            _region_decorators = [text({ optional: true, max: 80 })];
            _targetCapacity_decorators = [text({ optional: true, max: 200 })];
            _justification_decorators = [text({ max: 4000 })];
            _costCenter_decorators = [text({ optional: true, max: 100 })];
            _status_decorators = [text({ max: 40 })];
            _approverSub_decorators = [text({ optional: true, max: 200 })];
            _approvalNote_decorators = [text({ optional: true, max: 2000 })];
            _githubIssueUrl_decorators = [text({ optional: true, max: 400 })];
            _githubIssueNumber_decorators = [int({ optional: true })];
            _ownerSub_decorators = [text({ max: 200 })];
            _auditCreatedBy_decorators = [text({ max: 200 })];
            _auditCreatedAt_decorators = [date()];
            _auditUpdatedAt_decorators = [date({ optional: true })];
            __esDecorate(null, null, _id_decorators, { kind: "field", name: "id", static: false, private: false, access: { has: obj => "id" in obj, get: obj => obj.id, set: (obj, value) => { obj.id = value; } }, metadata: _metadata }, _id_initializers, _id_extraInitializers);
            __esDecorate(null, null, _requestType_decorators, { kind: "field", name: "requestType", static: false, private: false, access: { has: obj => "requestType" in obj, get: obj => obj.requestType, set: (obj, value) => { obj.requestType = value; } }, metadata: _metadata }, _requestType_initializers, _requestType_extraInitializers);
            __esDecorate(null, null, _displayName_decorators, { kind: "field", name: "displayName", static: false, private: false, access: { has: obj => "displayName" in obj, get: obj => obj.displayName, set: (obj, value) => { obj.displayName = value; } }, metadata: _metadata }, _displayName_initializers, _displayName_extraInitializers);
            __esDecorate(null, null, _environment_decorators, { kind: "field", name: "environment", static: false, private: false, access: { has: obj => "environment" in obj, get: obj => obj.environment, set: (obj, value) => { obj.environment = value; } }, metadata: _metadata }, _environment_initializers, _environment_extraInitializers);
            __esDecorate(null, null, _domain_decorators, { kind: "field", name: "domain", static: false, private: false, access: { has: obj => "domain" in obj, get: obj => obj.domain, set: (obj, value) => { obj.domain = value; } }, metadata: _metadata }, _domain_initializers, _domain_extraInitializers);
            __esDecorate(null, null, _capacitySku_decorators, { kind: "field", name: "capacitySku", static: false, private: false, access: { has: obj => "capacitySku" in obj, get: obj => obj.capacitySku, set: (obj, value) => { obj.capacitySku = value; } }, metadata: _metadata }, _capacitySku_initializers, _capacitySku_extraInitializers);
            __esDecorate(null, null, _region_decorators, { kind: "field", name: "region", static: false, private: false, access: { has: obj => "region" in obj, get: obj => obj.region, set: (obj, value) => { obj.region = value; } }, metadata: _metadata }, _region_initializers, _region_extraInitializers);
            __esDecorate(null, null, _targetCapacity_decorators, { kind: "field", name: "targetCapacity", static: false, private: false, access: { has: obj => "targetCapacity" in obj, get: obj => obj.targetCapacity, set: (obj, value) => { obj.targetCapacity = value; } }, metadata: _metadata }, _targetCapacity_initializers, _targetCapacity_extraInitializers);
            __esDecorate(null, null, _justification_decorators, { kind: "field", name: "justification", static: false, private: false, access: { has: obj => "justification" in obj, get: obj => obj.justification, set: (obj, value) => { obj.justification = value; } }, metadata: _metadata }, _justification_initializers, _justification_extraInitializers);
            __esDecorate(null, null, _costCenter_decorators, { kind: "field", name: "costCenter", static: false, private: false, access: { has: obj => "costCenter" in obj, get: obj => obj.costCenter, set: (obj, value) => { obj.costCenter = value; } }, metadata: _metadata }, _costCenter_initializers, _costCenter_extraInitializers);
            __esDecorate(null, null, _status_decorators, { kind: "field", name: "status", static: false, private: false, access: { has: obj => "status" in obj, get: obj => obj.status, set: (obj, value) => { obj.status = value; } }, metadata: _metadata }, _status_initializers, _status_extraInitializers);
            __esDecorate(null, null, _approverSub_decorators, { kind: "field", name: "approverSub", static: false, private: false, access: { has: obj => "approverSub" in obj, get: obj => obj.approverSub, set: (obj, value) => { obj.approverSub = value; } }, metadata: _metadata }, _approverSub_initializers, _approverSub_extraInitializers);
            __esDecorate(null, null, _approvalNote_decorators, { kind: "field", name: "approvalNote", static: false, private: false, access: { has: obj => "approvalNote" in obj, get: obj => obj.approvalNote, set: (obj, value) => { obj.approvalNote = value; } }, metadata: _metadata }, _approvalNote_initializers, _approvalNote_extraInitializers);
            __esDecorate(null, null, _githubIssueUrl_decorators, { kind: "field", name: "githubIssueUrl", static: false, private: false, access: { has: obj => "githubIssueUrl" in obj, get: obj => obj.githubIssueUrl, set: (obj, value) => { obj.githubIssueUrl = value; } }, metadata: _metadata }, _githubIssueUrl_initializers, _githubIssueUrl_extraInitializers);
            __esDecorate(null, null, _githubIssueNumber_decorators, { kind: "field", name: "githubIssueNumber", static: false, private: false, access: { has: obj => "githubIssueNumber" in obj, get: obj => obj.githubIssueNumber, set: (obj, value) => { obj.githubIssueNumber = value; } }, metadata: _metadata }, _githubIssueNumber_initializers, _githubIssueNumber_extraInitializers);
            __esDecorate(null, null, _ownerSub_decorators, { kind: "field", name: "ownerSub", static: false, private: false, access: { has: obj => "ownerSub" in obj, get: obj => obj.ownerSub, set: (obj, value) => { obj.ownerSub = value; } }, metadata: _metadata }, _ownerSub_initializers, _ownerSub_extraInitializers);
            __esDecorate(null, null, _auditCreatedBy_decorators, { kind: "field", name: "auditCreatedBy", static: false, private: false, access: { has: obj => "auditCreatedBy" in obj, get: obj => obj.auditCreatedBy, set: (obj, value) => { obj.auditCreatedBy = value; } }, metadata: _metadata }, _auditCreatedBy_initializers, _auditCreatedBy_extraInitializers);
            __esDecorate(null, null, _auditCreatedAt_decorators, { kind: "field", name: "auditCreatedAt", static: false, private: false, access: { has: obj => "auditCreatedAt" in obj, get: obj => obj.auditCreatedAt, set: (obj, value) => { obj.auditCreatedAt = value; } }, metadata: _metadata }, _auditCreatedAt_initializers, _auditCreatedAt_extraInitializers);
            __esDecorate(null, null, _auditUpdatedAt_decorators, { kind: "field", name: "auditUpdatedAt", static: false, private: false, access: { has: obj => "auditUpdatedAt" in obj, get: obj => obj.auditUpdatedAt, set: (obj, value) => { obj.auditUpdatedAt = value; } }, metadata: _metadata }, _auditUpdatedAt_initializers, _auditUpdatedAt_extraInitializers);
            __esDecorate(null, _classDescriptor = { value: _classThis }, _classDecorators, { kind: "class", name: _classThis.name, metadata: _metadata }, null, _classExtraInitializers);
            InfraRequest = _classThis = _classDescriptor.value;
            if (_metadata) Object.defineProperty(_classThis, Symbol.metadata, { enumerable: true, configurable: true, writable: true, value: _metadata });
            __runInitializers(_classThis, _classExtraInitializers);
        }
        id = __runInitializers(this, _id_initializers, void 0);
        // 'Capacity' | 'Workspace'
        requestType = (__runInitializers(this, _id_extraInitializers), __runInitializers(this, _requestType_initializers, void 0));
        // Requested capacity / workspace name.
        displayName = (__runInitializers(this, _requestType_extraInitializers), __runInitializers(this, _displayName_initializers, void 0));
        // 'dev' | 'test' | 'prod'
        environment = (__runInitializers(this, _displayName_extraInitializers), __runInitializers(this, _environment_initializers, void 0));
        // Governance domain the request belongs to (free-text natural key).
        domain = (__runInitializers(this, _environment_extraInitializers), __runInitializers(this, _domain_initializers, void 0));
        // --- Capacity-only fields ---
        // F-SKU, e.g. F2 / F8 / F64.
        capacitySku = (__runInitializers(this, _domain_extraInitializers), __runInitializers(this, _capacitySku_initializers, void 0));
        // Azure region, e.g. westus2 / eastus2.
        region = (__runInitializers(this, _capacitySku_extraInitializers), __runInitializers(this, _region_initializers, void 0));
        // --- Workspace-only field ---
        // Capacity (id or name) the workspace should be bound to.
        targetCapacity = (__runInitializers(this, _region_extraInitializers), __runInitializers(this, _targetCapacity_initializers, void 0));
        // Business context.
        justification = (__runInitializers(this, _targetCapacity_extraInitializers), __runInitializers(this, _justification_initializers, void 0));
        costCenter = (__runInitializers(this, _justification_extraInitializers), __runInitializers(this, _costCenter_initializers, void 0));
        // Workflow state: 'Pending' | 'Approved' | 'Rejected' | 'Submitted' | 'Completed'
        status = (__runInitializers(this, _costCenter_extraInitializers), __runInitializers(this, _status_initializers, void 0));
        // --- Approval ---
        approverSub = (__runInitializers(this, _status_extraInitializers), __runInitializers(this, _approverSub_initializers, void 0));
        approvalNote = (__runInitializers(this, _approverSub_extraInitializers), __runInitializers(this, _approvalNote_initializers, void 0));
        // --- GitHub linkage (stamped by the provisioning workflow) ---
        githubIssueUrl = (__runInitializers(this, _approvalNote_extraInitializers), __runInitializers(this, _githubIssueUrl_initializers, void 0));
        githubIssueNumber = (__runInitializers(this, _githubIssueUrl_extraInitializers), __runInitializers(this, _githubIssueNumber_initializers, void 0));
        // --- Ownership + audit (Rayfin does not auto-stamp these) ---
        ownerSub = (__runInitializers(this, _githubIssueNumber_extraInitializers), __runInitializers(this, _ownerSub_initializers, void 0));
        auditCreatedBy = (__runInitializers(this, _ownerSub_extraInitializers), __runInitializers(this, _auditCreatedBy_initializers, void 0));
        auditCreatedAt = (__runInitializers(this, _auditCreatedBy_extraInitializers), __runInitializers(this, _auditCreatedAt_initializers, void 0));
        auditUpdatedAt = (__runInitializers(this, _auditCreatedAt_extraInitializers), __runInitializers(this, _auditUpdatedAt_initializers, void 0));
        constructor() {
            __runInitializers(this, _auditUpdatedAt_extraInitializers);
        }
    };
    return InfraRequest = _classThis;
})();
export { InfraRequest };
