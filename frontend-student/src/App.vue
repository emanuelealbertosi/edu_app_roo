<script setup lang="ts">
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import { computed } from 'vue';
import { useAuthStore } from '@/stores/auth';

const authStore = useAuthStore();
const router = useRouter();
const route = useRoute();

// Nasconde la navbar nella pagina di login
const showNavbar = computed(() => route.name !== 'login');

const handleLogout = async () => {
  await authStore.logout();
  router.push('/login');
};
</script>

<template>
  <header v-if="showNavbar" class="main-navbar">
    <nav>
      <RouterLink to="/dashboard" class="nav-link">Dashboard</RouterLink>
      <RouterLink to="/shop" class="nav-link">Shop</RouterLink>
      <RouterLink to="/profile" class="nav-link">Profilo</RouterLink>
      <RouterLink to="/purchases" class="nav-link">Acquisti</RouterLink>
      <!-- <RouterLink to="/purchases" class="nav-link">Acquisti</RouterLink> -->
    </nav>
    <div class="user-actions">
       <span class="user-greeting">Ciao, {{ authStore.userFullName }}!</span>
       <button @click="handleLogout" class="logout-button-nav">Logout</button>
    </div>
  </header>
  <main class="main-content">
    <RouterView v-slot="{ Component }">
      <transition name="fade" mode="out-in">
        <component :is="Component" />
      </transition>
    </RouterView>
  </main>
</template>

<style scoped>
.main-navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2rem;
  background-color: #333; /* Sfondo scuro per la navbar */
  color: white;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
  position: fixed; /* Rende la navbar fissa */
  top: 0;
  left: 0;
  width: 100%;
  z-index: 1000; /* Assicura che sia sopra altri elementi */
}

.main-navbar nav {
  display: flex;
  gap: 1.5rem;
}

.nav-link {
  color: #eee;
  text-decoration: none;
  font-weight: 500;
  padding: 0.5rem 0;
  border-bottom: 2px solid transparent;
  transition: color 0.2s, border-bottom-color 0.2s;
}

.nav-link:hover,
.nav-link.router-link-exact-active { /* Stile per il link attivo */
  color: white;
  border-bottom-color: #007bff; /* Colore primario per sottolineatura */
}

.user-actions {
    display: flex;
    align-items: center;
    gap: 1rem;
}

.user-greeting {
    font-size: 0.9em;
    color: #ccc;
}

.logout-button-nav {
  background-color: #dc3545; /* Rosso */
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9em;
  transition: background-color 0.2s;
}

.logout-button-nav:hover {
  background-color: #c82333; /* Rosso più scuro */
}

/* Aggiunge un po' di padding al contenuto principale per non sovrapporsi alla navbar fissa (se fosse fissa) */
.main-content {
  /* Aggiunge padding pari all'altezza stimata della navbar + un po' di margine */
  /* Calcolare l'altezza esatta potrebbe richiedere JS o essere approssimato */
  padding-top: calc(2rem + 32px + 1rem); /* padding navbar + altezza stimata testo/bottoni + margine extra */
  /* Alternativa più semplice: altezza fissa */
  /* padding-top: 70px; */
}

/* Media Query per schermi piccoli */
@media (max-width: 768px) {
  .main-navbar {
    padding: 0.8rem 1rem; /* Riduci padding */
    flex-direction: column; /* Impila elementi verticalmente */
    align-items: flex-start; /* Allinea a sinistra */
  }
  .main-navbar nav {
      gap: 1rem; /* Riduci gap link */
      margin-bottom: 0.5rem; /* Spazio sotto i link */
      flex-wrap: wrap; /* Manda a capo i link se non ci stanno */
  }
   .user-actions {
       width: 100%; /* Occupa tutta la larghezza */
       justify-content: space-between; /* Spinge saluto e logout ai lati */
   }
   .user-greeting {
       /* Potrebbe essere nascosto su schermi molto piccoli se necessario */
       /* display: none; */
   }
   .main-content {
       /* Potrebbe essere necessario aggiustare il padding-top */
       padding-top: calc(1.6rem + 60px + 1rem); /* Altezza navbar stimata maggiore */
   }
}

/* Stili per la transizione fade */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 480px) {
    .main-navbar nav {
        gap: 0.8rem;
    }
    .nav-link {
        font-size: 0.9em;
    }
    .user-greeting {
        display: none; /* Nascondi saluto su schermi molto piccoli */
    }
     .user-actions {
       justify-content: flex-end; /* Allinea solo il logout a destra */
   }
}
</style>

