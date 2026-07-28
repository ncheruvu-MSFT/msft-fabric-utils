import { useCallback, useEffect, useRef, useState } from 'react';
import {
  Badge,
  Body1,
  Button,
  Caption1,
  OverlayDrawer,
  DrawerBody,
  DrawerHeader,
  DrawerHeaderTitle,
  Spinner,
  Textarea,
  makeStyles,
  shorthands,
  tokens,
} from '@fluentui/react-components';
import {
  CloudRegular,
  DismissRegular,
  PlugDisconnectedRegular,
  SendRegular,
  SparkleRegular,
} from '@fluentui/react-icons';

export interface ChatMessage {
  role: 'user' | 'agent';
  text: string;
  source?: 'agent' | 'local';
}

const useStyles = makeStyles({
  body: {
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    ...shorthands.gap('12px'),
  },
  messages: {
    flexGrow: 1,
    overflowY: 'auto',
    display: 'flex',
    flexDirection: 'column',
    ...shorthands.gap('10px'),
    ...shorthands.padding('4px', '2px'),
  },
  bubble: {
    maxWidth: '88%',
    ...shorthands.padding('8px', '12px'),
    ...shorthands.borderRadius(tokens.borderRadiusLarge),
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-word',
  },
  user: {
    alignSelf: 'flex-end',
    backgroundColor: tokens.colorBrandBackground,
    color: tokens.colorNeutralForegroundOnBrand,
  },
  agent: {
    alignSelf: 'flex-start',
    backgroundColor: tokens.colorNeutralBackground3,
    color: tokens.colorNeutralForeground1,
  },
  empty: {
    ...shorthands.padding('16px'),
    textAlign: 'center',
    color: tokens.colorNeutralForeground3,
  },
  inputRow: {
    display: 'flex',
    ...shorthands.gap('8px'),
    alignItems: 'flex-end',
  },
  textarea: {
    flexGrow: 1,
  },
  suggestions: {
    display: 'flex',
    flexWrap: 'wrap',
    ...shorthands.gap('6px'),
  },
});

export interface ChatPanelProps {
  open: boolean;
  onClose: () => void;
  title: string;
  subtitle: string;
  suggestions: string[];
  onAsk: (question: string) => Promise<{ text: string; source: 'agent' | 'local' }>;
}

/** Render markdown-ish lines (bold + bullets) without pulling in a parser. */
function renderText(text: string): JSX.Element {
  const lines = text.split('\n');
  return (
    <>
      {lines.map((line, i) => {
        const parts = line.split(/(\*\*[^*]+\*\*|_[^_]+_)/g).filter(Boolean);
        return (
          <div key={i}>
            {parts.map((p, j) => {
              if (p.startsWith('**') && p.endsWith('**')) {
                return <strong key={j}>{p.slice(2, -2)}</strong>;
              }
              if (p.startsWith('_') && p.endsWith('_')) {
                return <em key={j}>{p.slice(1, -1)}</em>;
              }
              return <span key={j}>{p}</span>;
            })}
          </div>
        );
      })}
    </>
  );
}

export function ChatPanel(props: ChatPanelProps) {
  const styles = useStyles();
  const { open, onClose, title, subtitle, suggestions, onAsk } = props;
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages, busy]);

  const send = useCallback(
    async (question: string) => {
      const q = question.trim();
      if (!q || busy) return;
      setInput('');
      setMessages((m) => [...m, { role: 'user', text: q }]);
      setBusy(true);
      try {
        const ans = await onAsk(q);
        setMessages((m) => [
          ...m,
          { role: 'agent', text: ans.text, source: ans.source },
        ]);
      } catch (e) {
        setMessages((m) => [
          ...m,
          { role: 'agent', text: `Error: ${String(e)}`, source: 'local' },
        ]);
      } finally {
        setBusy(false);
      }
    },
    [busy, onAsk],
  );

  return (
    <OverlayDrawer
      open={open}
      onOpenChange={(_, d) => !d.open && onClose()}
      position="end"
      size="medium"
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
          <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <SparkleRegular />
            {title}
          </span>
        </DrawerHeaderTitle>
        <Caption1>{subtitle}</Caption1>
      </DrawerHeader>

      <DrawerBody>
        <div className={styles.body}>
          <div className={styles.messages} ref={scrollRef}>
            {messages.length === 0 && (
              <div className={styles.empty}>
                <Body1>Ask a question about your data to get started.</Body1>
              </div>
            )}
            {messages.map((m, i) => (
              <div
                key={i}
                className={`${styles.bubble} ${
                  m.role === 'user' ? styles.user : styles.agent
                }`}
              >
                {m.role === 'agent' && m.source && (
                  <Badge
                    appearance="tint"
                    size="small"
                    color={m.source === 'agent' ? 'success' : 'informative'}
                    icon={
                      m.source === 'agent' ? (
                        <CloudRegular />
                      ) : (
                        <PlugDisconnectedRegular />
                      )
                    }
                    style={{ marginBottom: 4 }}
                  >
                    {m.source === 'agent' ? 'Data agent' : 'Local'}
                  </Badge>
                )}
                {renderText(m.text)}
              </div>
            ))}
            {busy && (
              <div className={`${styles.bubble} ${styles.agent}`}>
                <Spinner size="tiny" label="Thinking…" />
              </div>
            )}
          </div>

          {messages.length === 0 && (
            <div className={styles.suggestions}>
              {suggestions.map((s) => (
                <Button
                  key={s}
                  size="small"
                  appearance="outline"
                  onClick={() => void send(s)}
                >
                  {s}
                </Button>
              ))}
            </div>
          )}

          <div className={styles.inputRow}>
            <Textarea
              className={styles.textarea}
              value={input}
              placeholder="Ask about your data…"
              resize="vertical"
              onChange={(_, d) => setInput(d.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  void send(input);
                }
              }}
            />
            <Button
              appearance="primary"
              icon={<SendRegular />}
              disabled={busy || !input.trim()}
              onClick={() => void send(input)}
              aria-label="Send"
            />
          </div>
        </div>
      </DrawerBody>
    </OverlayDrawer>
  );
}
