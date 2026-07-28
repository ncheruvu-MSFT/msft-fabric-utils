import {
  Badge,
  Body1,
  Button,
  Caption1,
  Card,
  Divider,
  Dropdown,
  DrawerBody,
  DrawerHeader,
  DrawerHeaderTitle,
  Field,
  Input,
  Option,
  OverlayDrawer,
  Textarea,
  Title3,
  makeStyles,
  shorthands,
  tokens,
} from '@fluentui/react-components';
import {
  AddRegular,
  ArrowDownRegular,
  ArrowUpRegular,
  DeleteRegular,
  DismissRegular,
  FlowRegular,
} from '@fluentui/react-icons';
import {
  ApprovalStage,
  ApproverType,
  Classification,
  WorkflowTemplate,
} from './dataClient';

const APPROVER_TYPES: ApproverType[] = [
  'Manager',
  'Data owner',
  'Data steward',
  'Security admin',
  'Custom',
];

const CLASSIFICATIONS: Classification[] = [
  'Public',
  'Internal',
  'Confidential',
  'Highly Confidential',
  'PII',
];

const useStyles = makeStyles({
  body: { display: 'flex', flexDirection: 'column', ...shorthands.gap('16px') },
  list: { display: 'flex', flexWrap: 'wrap', ...shorthands.gap('8px') },
  card: {
    display: 'flex',
    flexDirection: 'column',
    ...shorthands.gap('12px'),
    ...shorthands.padding('16px'),
  },
  row: { display: 'flex', ...shorthands.gap('8px'), flexWrap: 'wrap' },
  stage: {
    display: 'flex',
    flexDirection: 'column',
    ...shorthands.gap('8px'),
    ...shorthands.padding('12px'),
    ...shorthands.borderRadius(tokens.borderRadiusMedium),
    backgroundColor: tokens.colorNeutralBackground2,
  },
  stageHead: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    ...shorthands.gap('8px'),
  },
  grow: { flexGrow: 1, minWidth: '160px' },
  chain: { display: 'flex', alignItems: 'center', flexWrap: 'wrap', ...shorthands.gap('4px') },
});

function newStage(): ApprovalStage {
  return {
    id:
      typeof crypto !== 'undefined' && 'randomUUID' in crypto
        ? crypto.randomUUID()
        : `s-${Date.now()}`,
    name: 'New stage',
    approverType: 'Manager',
    slaHours: 48,
  };
}

export interface WorkflowEditorProps {
  open: boolean;
  onClose: () => void;
  templates: WorkflowTemplate[];
  onChange: (templates: WorkflowTemplate[]) => void;
}

export function WorkflowEditor({
  open,
  onClose,
  templates,
  onChange,
}: WorkflowEditorProps) {
  const styles = useStyles();

  const update = (id: string, patch: Partial<WorkflowTemplate>) =>
    onChange(templates.map((t) => (t.id === id ? { ...t, ...patch } : t)));

  const updateStage = (
    tid: string,
    sid: string,
    patch: Partial<ApprovalStage>,
  ) =>
    onChange(
      templates.map((t) =>
        t.id === tid
          ? {
              ...t,
              stages: t.stages.map((s) =>
                s.id === sid ? { ...s, ...patch } : s,
              ),
            }
          : t,
      ),
    );

  const addStage = (tid: string) =>
    onChange(
      templates.map((t) =>
        t.id === tid ? { ...t, stages: [...t.stages, newStage()] } : t,
      ),
    );

  const removeStage = (tid: string, sid: string) =>
    onChange(
      templates.map((t) =>
        t.id === tid
          ? { ...t, stages: t.stages.filter((s) => s.id !== sid) }
          : t,
      ),
    );

  const moveStage = (tid: string, idx: number, delta: number) =>
    onChange(
      templates.map((t) => {
        if (t.id !== tid) return t;
        const stages = [...t.stages];
        const j = idx + delta;
        if (j < 0 || j >= stages.length) return t;
        [stages[idx], stages[j]] = [stages[j], stages[idx]];
        return { ...t, stages };
      }),
    );

  const toggleClassification = (t: WorkflowTemplate, c: Classification) => {
    if (t.appliesTo === '*') {
      update(t.id, { appliesTo: [c] });
      return;
    }
    const has = t.appliesTo.includes(c);
    update(t.id, {
      appliesTo: has
        ? t.appliesTo.filter((x) => x !== c)
        : [...t.appliesTo, c],
    });
  };

  const addTemplate = () =>
    onChange([
      ...templates,
      {
        id:
          typeof crypto !== 'undefined' && 'randomUUID' in crypto
            ? crypto.randomUUID()
            : `wf-${Date.now()}`,
        name: 'New workflow',
        description: 'Describe when this approval path applies.',
        appliesTo: [],
        stages: [newStage()],
      },
    ]);

  const removeTemplate = (id: string) =>
    onChange(templates.filter((t) => t.id !== id));

  return (
    <OverlayDrawer
      position="end"
      open={open}
      onOpenChange={(_, d) => !d.open && onClose()}
      size="large"
    >
      <DrawerHeader>
        <DrawerHeaderTitle
          action={
            <Button
              appearance="subtle"
              icon={<DismissRegular />}
              aria-label="Close"
              onClick={onClose}
            />
          }
        >
          Approval workflow templates
        </DrawerHeaderTitle>
      </DrawerHeader>
      <DrawerBody>
        <div className={styles.body}>
          <Caption1>
            Data-map admins and data owners configure the self-service approval
            paths here. Each template binds to one or more classifications and
            routes a request through an ordered chain of approvers (the
            requester&apos;s manager is resolved from Entra automatically).
          </Caption1>

          {templates.map((t) => (
            <Card key={t.id} className={styles.card}>
              <div className={styles.row}>
                <Field label="Workflow name" className={styles.grow}>
                  <Input
                    value={t.name}
                    onChange={(_, d) => update(t.id, { name: d.value })}
                  />
                </Field>
                <Button
                  appearance="subtle"
                  icon={<DeleteRegular />}
                  onClick={() => removeTemplate(t.id)}
                  disabled={templates.length <= 1}
                >
                  Delete
                </Button>
              </div>

              <Field label="Description">
                <Textarea
                  value={t.description}
                  onChange={(_, d) => update(t.id, { description: d.value })}
                  rows={2}
                />
              </Field>

              <Field label="Applies to classifications">
                <div className={styles.list}>
                  {CLASSIFICATIONS.map((c) => {
                    const active =
                      t.appliesTo !== '*' && t.appliesTo.includes(c);
                    return (
                      <Button
                        key={c}
                        size="small"
                        appearance={active ? 'primary' : 'outline'}
                        onClick={() => toggleClassification(t, c)}
                      >
                        {c}
                      </Button>
                    );
                  })}
                </div>
              </Field>

              {/* visual chain preview */}
              <div className={styles.chain}>
                <Badge appearance="outline">Requester</Badge>
                {t.stages.map((s) => (
                  <span key={s.id} className={styles.chain}>
                    <Caption1>→</Caption1>
                    <Badge appearance="tint" color="brand">
                      {s.approverUpn?.trim() || s.approverType}
                    </Badge>
                  </span>
                ))}
                <Caption1>→</Caption1>
                <Badge appearance="tint" color="success">
                  Access granted
                </Badge>
              </div>

              <Divider />
              <Title3 as="h4" style={{ fontSize: tokens.fontSizeBase300 }}>
                Approval stages
              </Title3>

              {t.stages.map((s, idx) => (
                <div className={styles.stage} key={s.id}>
                  <div className={styles.stageHead}>
                    <Body1>Stage {idx + 1}</Body1>
                    <div className={styles.row}>
                      <Button
                        size="small"
                        appearance="subtle"
                        icon={<ArrowUpRegular />}
                        aria-label="Move up"
                        disabled={idx === 0}
                        onClick={() => moveStage(t.id, idx, -1)}
                      />
                      <Button
                        size="small"
                        appearance="subtle"
                        icon={<ArrowDownRegular />}
                        aria-label="Move down"
                        disabled={idx === t.stages.length - 1}
                        onClick={() => moveStage(t.id, idx, 1)}
                      />
                      <Button
                        size="small"
                        appearance="subtle"
                        icon={<DeleteRegular />}
                        aria-label="Remove stage"
                        disabled={t.stages.length <= 1}
                        onClick={() => removeStage(t.id, s.id)}
                      />
                    </div>
                  </div>
                  <div className={styles.row}>
                    <Field label="Stage name" className={styles.grow}>
                      <Input
                        value={s.name}
                        onChange={(_, d) =>
                          updateStage(t.id, s.id, { name: d.value })
                        }
                      />
                    </Field>
                    <Field label="Approver">
                      <Dropdown
                        value={s.approverType}
                        selectedOptions={[s.approverType]}
                        onOptionSelect={(_, d) =>
                          updateStage(t.id, s.id, {
                            approverType:
                              (d.optionValue as ApproverType) ?? 'Manager',
                          })
                        }
                      >
                        {APPROVER_TYPES.map((a) => (
                          <Option key={a} value={a}>
                            {a}
                          </Option>
                        ))}
                      </Dropdown>
                    </Field>
                    <Field label="SLA (hours)">
                      <Input
                        type="number"
                        value={String(s.slaHours ?? '')}
                        onChange={(_, d) =>
                          updateStage(t.id, s.id, {
                            slaHours: Number(d.value) || undefined,
                          })
                        }
                        style={{ width: '90px' }}
                      />
                    </Field>
                  </div>
                  {(s.approverType === 'Custom' ||
                    s.approverType === 'Security admin') && (
                    <Field
                      label={
                        s.approverType === 'Custom'
                          ? 'Approver UPN'
                          : 'Approver UPN (override)'
                      }
                    >
                      <Input
                        value={s.approverUpn ?? ''}
                        onChange={(_, d) =>
                          updateStage(t.id, s.id, { approverUpn: d.value })
                        }
                        placeholder="name@contoso.com"
                      />
                    </Field>
                  )}
                </div>
              ))}

              <Button
                appearance="secondary"
                icon={<AddRegular />}
                onClick={() => addStage(t.id)}
              >
                Add stage
              </Button>
            </Card>
          ))}

          <Button
            appearance="primary"
            icon={<FlowRegular />}
            onClick={addTemplate}
          >
            New workflow template
          </Button>
        </div>
      </DrawerBody>
    </OverlayDrawer>
  );
}
