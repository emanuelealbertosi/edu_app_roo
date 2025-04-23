import mitt from 'mitt';

// Definisci i tipi di evento (opzionale ma consigliato per TypeScript)
type Events = {
  'open-add-subject-modal': void;
  'open-add-topic-modal': void;
  'open-add-lesson-modal': void;
};

const emitter = mitt<Events>();

export default emitter;