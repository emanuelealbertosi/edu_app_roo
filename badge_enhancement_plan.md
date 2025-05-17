# Piano di Progettazione: Miglioramento Badge Studente e Gestione Media

## 1. Introduzione e Obiettivi

Questo documento descrive il piano per implementare miglioramenti significativi alla visualizzazione dei badge per gli studenti e alla gestione dei media associati nell'interfaccia di amministrazione di Django.

Gli obiettivi principali sono:

*   **Migliorare l'esperienza utente nel frontend studente:**
    *   Aumentare la dimensione dei badge.
    *   Introdurre il supporto per badge video (MP4) e GIF animate.
    *   Differenziare visivamente i badge guadagnati da quelli non guadagnati, con anteprime statiche (thumbnail) per i media animati non guadagnati.
*   **Potenziare le capacità di gestione nel backend (Django Admin):**
    *   Permettere l'upload di file video MP4 e GIF animate per i badge, oltre alle immagini statiche.
    *   Fornire un campo opzionale per un'immagine di anteprima (thumbnail) per video e GIF.
    *   Introdurre un "Media Manager" per visualizzare e rimuovere i file media (immagini, GIF, video, thumbnail) associati ai badge.

## 2. Riepilogo dei Requisiti Chiave

*   **Dimensione Badge Frontend:** Aumento del 50% rispetto alla dimensione attuale.
*   **Tipi di Media per Badge:**
    *   Immagini statiche (JPG, PNG, SVG).
    *   Immagini animate (GIF).
    *   Video (MP4).
*   **Visualizzazione Badge Guadagnati:**
    *   Video MP4: Riproduzione automatica in loop, senza audio, senza controlli.
    *   GIF: Animate.
    *   Immagini statiche: Visualizzazione normale.
    *   Colori pieni, senza lucchetto.
*   **Visualizzazione Badge Non Guadagnati:**
    *   Stile grigio/desaturato.
    *   Icona a forma di lucchetto colorata sovrapposta.
    *   Se il media principale è un video MP4 o una GIF animata e un `thumbnail` è stato caricato, mostrare il `thumbnail` (immagine statica).
    *   Altrimenti (immagine statica, o video/GIF senza `thumbnail` fornito), mostrare il media principale (che sarà desaturato).
*   **Campo Thumbnail (Backend):** Un campo `ImageField` opzionale nel modello `Badge` per caricare un'anteprima statica per video e GIF.
*   **Media Manager (Backend):**
    *   Approccio: Gestione diretta tramite l'admin del modello `Badge`. Un Media Manager separato e dedicato è rimandato. La pulizia di file orfani potrà essere gestita con script di manutenzione futuri se necessario.
    *   Funzionalità: L'admin del modello `Badge` permetterà di caricare, modificare e rimuovere (impostando il campo a `None`) i file `file` e `thumbnail` associati a un badge.

## 3. Piano Dettagliato

### Fase 1: Modifiche al Backend (Django)

1.  **Aggiornamento Modello `Badge` ([`apps/rewards/models.py`](apps/rewards/models.py))**
    *   Modificare il campo `image` esistente in `file = models.FileField(upload_to='badges/files/', help_text=_('File principale del badge (immagine, GIF, o video MP4).'))`.
        *   Aggiungere validatori per tipi di file: JPG, PNG, SVG, GIF, MP4.
    *   Aggiungere `media_type = models.CharField(max_length=20, choices=MediaType.choices, editable=False, help_text=_('Tipo di media, impostato automaticamente.'))`.
        *   `MediaType.choices` includerà `IMAGE_STATIC`, `IMAGE_GIF`, `VIDEO_MP4`.
        *   Popolare `media_type` automaticamente nel metodo `save()` del modello analizzando l'estensione o il content type del `file` caricato.
    *   Aggiungere `thumbnail = models.ImageField(upload_to='badges/thumbnails/', null=True, blank=True, help_text=_('Anteprima statica opzionale per video o GIF animate, mostrata se il badge non è guadagnato.'))`.
        *   Validatori per tipi di file immagine (JPG, PNG, SVG).
    *   Creare e applicare le migrazioni Django (`makemigrations rewards`, `migrate rewards`).

2.  **Aggiornamento Django Admin per `Badge` ([`apps/rewards/admin.py`](apps/rewards/admin.py))**
    *   Nella classe `BadgeAdmin`:
        *   Assicurare che i form per `file` e `thumbnail` permettano l'upload dei tipi di file corretti.
        *   Visualizzare anteprime per `file` (immagine, o un link/placeholder per video/GIF se l'anteprima inline è complessa) e per `thumbnail` nella `change_form`.
        *   Mostrare `media_type` come campo di sola lettura.
        *   Considerare l'uso di `django-admin-thumbnails` o simili per anteprime migliori nella `list_display` se necessario.

3.  **Gestione Media tramite Admin `Badge` (Sostituisce Media Manager Separato per Ora)**
    *   L'interfaccia di amministrazione per il modello `Badge` (come configurata al punto 2) sarà il mezzo principale per gestire i file media.
    *   Gli amministratori potranno caricare nuovi file per i campi `file` e `thumbnail`.
    *   Per rimuovere un file associato a un badge, l'amministratore potrà cancellare il riferimento al file nel campo specifico (es. `file` o `thumbnail`) e salvare il badge. Questo lascerà il file sul disco come "orfano".
    *   Non verrà implementato un Media Manager separato con una vista aggregata di tutti i file in questa fase, per evitare la complessità e l'errore riscontrato con l'approccio del modello proxy.
    *   La pulizia periodica di file media orfani (non più referenziati da alcun badge) potrà essere considerata come un task di manutenzione separato da implementare con uno script di management Django in futuro, se ritenuto necessario.

4.  **Aggiornamento Serializzatori e API ([`apps/rewards/serializers.py`](apps/rewards/serializers.py), [`apps/rewards/views.py`](apps/rewards/views.py))**
    *   Modificare `BadgeSerializer` (o equivalente) per includere:
        *   `file_url`: URL completo al campo `file`.
        *   `media_type`: Il valore del campo `media_type`.
        *   `thumbnail_url`: URL completo al campo `thumbnail` (se presente, altrimenti `null`).
    *   Modificare le viste API (es. quelle per la dashboard studente, pagina trofei) per aggiungere un campo `is_earned` (booleano) a ciascun oggetto badge serializzato, indicante se lo studente che fa la richiesta ha guadagnato quel badge. Questo richiederà di accedere ai dati di `EarnedBadge` relativi allo studente e al badge.

### Fase 2: Modifiche al Frontend (Vue.js - `frontend-student`)

1.  **Aggiornamento Componenti Badge (es. [`frontend-student/src/components/common/AnimatedBadge.vue`](frontend-student/src/components/common/AnimatedBadge.vue))**
    *   Il componente riceverà le proprietà: `fileUrl`, `mediaType`, `thumbnailUrl` (può essere `null`), `isEarned` (booleano), `badgeName`.
    *   **Stili CSS:**
        *   Aumentare la dimensione base del badge del 50%.
        *   Classe per lo stato "non guadagnato": `filter: grayscale(100%); opacity: 0.7;` (o simile per desaturazione).
        *   Elemento per sovrapporre l'icona del lucchetto (es. usando pseudo-elementi `::before` o `::after` con un'immagine di sfondo SVG/PNG del lucchetto).
    *   **Logica Template (Vue):**
        ```html
        <div :class="['badge-container', { 'not-earned': !isEarned }]">
          <!-- Lucchetto sovrapposto se non guadagnato -->
          <div v-if="!isEarned" class="lock-overlay"></div>

          <!-- Caso: Non Guadagnato E (Video o GIF con Thumbnail) -->
          <img v-if="!isEarned && (mediaType === 'VIDEO_MP4' || mediaType === 'IMAGE_GIF') && thumbnailUrl"
               :src="thumbnailUrl" :alt="badgeName + ' thumbnail'" class="badge-media static-preview">

          <!-- Caso: Non Guadagnato E (Immagine Statica, o Video/GIF senza Thumbnail) -->
          <img v-else-if="!isEarned && (mediaType === 'IMAGE_STATIC' || !thumbnailUrl)"
               :src="fileUrl" :alt="badgeName" class="badge-media">

          <!-- Caso: Guadagnato E Video -->
          <video v-else-if="isEarned && mediaType === 'VIDEO_MP4'"
                 :src="fileUrl" class="badge-media" autoplay loop muted playsinline
                 :aria-label="badgeName"></video>

          <!-- Caso: Guadagnato E Immagine (Statica o GIF) -->
          <img v-else-if="isEarned && (mediaType === 'IMAGE_STATIC' || mediaType === 'IMAGE_GIF')"
               :src="fileUrl" :alt="badgeName" class="badge-media">
        </div>
        ```
    *   Assicurarsi che gli stili per `.badge-media` e `.static-preview` gestiscano correttamente le dimensioni.

2.  **Aggiornamento Viste Dashboard e Pagina Trofei ([`frontend-student/src/views/DashboardView.vue`](frontend-student/src/views/DashboardView.vue), [`frontend-student/src/views/BadgesView.vue`](frontend-student/src/views/BadgesView.vue))**
    *   Assicurare che il layout delle viste si adatti correttamente ai badge più grandi.
    *   Verificare che i dati recuperati dagli store Pinia (es. `rewardsStore`) includano `fileUrl`, `mediaType`, `thumbnailUrl`, e `isEarned` per ogni badge e li passino correttamente ai componenti.

### Fase 3: Test

1.  **Test Backend:**
    *   Upload di tutti i tipi di file supportati (JPG, PNG, SVG, GIF, MP4) per il campo `file` del `Badge` tramite l'admin `BadgeAdmin`.
    *   Upload di immagini per il campo `thumbnail` tramite l'admin `BadgeAdmin`.
    *   Verifica della corretta impostazione automatica di `media_type`.
    *   Verifica che la rimozione di un file da un campo `file` o `thumbnail` in `BadgeAdmin` (e il salvataggio) non causi errori e che il riferimento venga effettivamente rimosso dal modello Badge (il file rimarrà sul disco come orfano, come da decisione).
    *   Correttezza dei dati esposti dalle API, incluso il flag `is_earned` per lo studente.
2.  **Test Frontend:**
    *   Corretta visualizzazione dei badge (dimensioni, colori, lucchetto) per stati guadagnati/non guadagnati.
    *   Visualizzazione del `thumbnail` per video/GIF non guadagnati, se il thumbnail è presente.
    *   Visualizzazione del media principale desaturato per video/GIF non guadagnati, se il thumbnail non è presente.
    *   Riproduzione corretta dei video (loop, muted, no controls) e animazione delle GIF per i badge guadagnati.
    *   Testare su diversi browser e verificare la responsività.
3.  **Test End-to-End:**
    *   Flusso completo: un admin crea un badge video con thumbnail; uno studente non lo ha ancora guadagnato (vede thumbnail grigio con lucchetto); lo studente completa l'azione per guadagnare il badge; lo studente ora vede il video in loop a colori.

## 4. Diagramma di Flusso

```mermaid
graph TD
    A[Inizio Richiesta Utente] --> B{Modifiche Backend};
    B --> B1[Aggiorna Modello Badge: FileField, media_type (distingue GIF), thumbnail (opzionale)];
    B1 --> B2[Migrazioni DB];
    B --> B3[Aggiorna Admin Django per Badge: upload MP4/GIF/IMG, upload thumbnail. Gestione media tramite questo admin.];
    B --> B4[Media Manager separato rimandato. Pulizia orfani futura.];
    B --> B5[Aggiorna Serializer/API Rewards: include media_type, file_url, thumbnail_url, e flag 'is_earned'];

    A --> C{Modifiche Frontend};
    C --> C1[Aggiorna Componente Badge: +50% size];
    C1 --> C1a[Logica Display: if is_earned -> full color, media animato];
    C1 --> C1b[Logica Display: if NOT is_earned -> grigio, lucchetto, mostra thumbnail (se video/GIF & presente) o img/video desaturato];
    C1 --> C2[CSS per dimensioni, desaturazione, lucchetto];
    C --> C3[Aggiorna Viste: Dashboard, Pagina Trofei];
    C3 --> C4[Adatta layout];
    C3 --> C5[Gestione dati API (is_earned, thumbnail_url)];

    B2 --> D{Test Backend};
    B3 --> D;
    B4 --> D;
    B5 --> D;

    C2 --> E{Test Frontend};
    C4 --> E;
    C5 --> E;

    D --> F[Test E2E];
    E --> F;
    F --> G[Fine Implementazione];