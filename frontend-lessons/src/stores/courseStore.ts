import { defineStore } from 'pinia';
import { courseService } from '@/services/courseService';
import type { Course, UDA } from '@/types/uda';

interface CourseState {
  courses: Course[];
  currentCourse: Course | null;
  loading: boolean;
  error: string | null;
}

export const useCourseStore = defineStore('course', {
  state: (): CourseState => ({
    courses: [],
    currentCourse: null,
    loading: false,
    error: null,
  }),
  actions: {
    async fetchCourses() {
      this.loading = true;
      this.error = null;
      try {
        const data = await courseService.getCourses();
        this.courses = data;
      } catch (err) {
        this.error = (err as Error).message || 'Failed to fetch courses';
        this.courses = [];
      } finally {
        this.loading = false;
      }
    },

    async fetchCourse(id: number) {
      this.loading = true;
      this.error = null;
      try {
        const data = await courseService.getCourse(id);
        this.currentCourse = data;
        // Se le UDA non sono caricate di default con il corso, potremmo volerle caricare qui
        // if (this.currentCourse && !this.currentCourse.udas) {
        //   this.currentCourse.udas = await this.fetchUdasForCourse(id);
        // }

      } catch (err) {
        this.error = (err as Error).message || `Failed to fetch course ${id}`;
        this.currentCourse = null;
      } finally {
        this.loading = false;
      }
    },

    async createCourse(courseData: Pick<Course, 'name' | 'description'>): Promise<Course | undefined> {
      this.loading = true;
      this.error = null;
      try {
        const newCourse = await courseService.createCourse(courseData);
        this.courses.push(newCourse);
        this.currentCourse = newCourse;
        return newCourse;
      } catch (err) {
        this.error = (err as Error).message || 'Failed to create course';
        throw err;
      } finally {
        this.loading = false;
      }
    },

    async updateCourse(id: number, courseData: Partial<Pick<Course, 'name' | 'description'>>): Promise<Course | undefined> {
      this.loading = true;
      this.error = null;
      try {
        const updatedCourse = await courseService.updateCourse(id, courseData);
        const index = this.courses.findIndex(c => c.id === id);
        if (index !== -1) {
          this.courses[index] = updatedCourse;
        }
        if (this.currentCourse?.id === id) {
          this.currentCourse = updatedCourse;
        }
        return updatedCourse;
      } catch (err) {
        this.error = (err as Error).message || 'Failed to update course';
        throw err;
      } finally {
        this.loading = false;
      }
    },

    async deleteCourse(id: number) {
      this.loading = true;
      this.error = null;
      try {
        await courseService.deleteCourse(id);
        this.courses = this.courses.filter(c => c.id !== id);
        if (this.currentCourse?.id === id) {
          this.currentCourse = null;
        }
      } catch (err) {
        this.error = (err as Error).message || 'Failed to delete course';
        throw err;
      } finally {
        this.loading = false;
      }
    },

    async copyCourse(courseId: number): Promise<Course | undefined> {
      this.loading = true;
      this.error = null;
      try {
        const newCourse = await courseService.copyCourse(courseId);
        // Per semplicità, ricarichiamo la lista dei corsi per vedere la copia.
        // In alternativa, si potrebbe aggiungere 'newCourse' all'array 'this.courses'.
        await this.fetchCourses();
        return newCourse;
      } catch (err) {
        this.error = (err as Error).message || 'Failed to copy course';
        throw err;
      } finally {
        this.loading = false;
      }
    },

    async fetchUdasForCourse(courseId: number): Promise<UDA[]> {
      this.loading = true; // Potrebbe essere un loading specifico per le UDA del corso
      this.error = null;
      try {
        const udas = await courseService.getUdasForCourse(courseId);
        if (this.currentCourse?.id === courseId) {
          this.currentCourse.udas = udas;
        }
        return udas;
      } catch (err) {
        this.error = (err as Error).message || `Failed to fetch UDAs for course ${courseId}`;
        if (this.currentCourse?.id === courseId) {
            this.currentCourse.udas = [];
        }
        return [];
      } finally {
        this.loading = false;
      }
    },
    
    async reorderUdasInCourse(courseId: number, udaIds: number[]) {
        this.loading = true;
        this.error = null;
        try {
            await courseService.reorderUdasInCourse(courseId, udaIds);
            // Aggiorna l'ordine localmente rifacendo il fetch delle UDA per semplicità,
            // o aggiorna l'array this.currentCourse.udas manualmente se preferisci ottimizzare.
            if (this.currentCourse?.id === courseId) {
               await this.fetchUdasForCourse(courseId);
            }
        } catch (err) {
            this.error = (err as Error).message || 'Failed to reorder UDAs';
            throw err;
        } finally {
            this.loading = false;
        }
    },
    async exportUdas(courseId: number, format: 'docx' | 'pdf'): Promise<void> {
      // Non impostiamo loading/error qui perché il servizio gestirà il download
      // e non c'è uno stato specifico dello store da aggiornare con il risultato diretto.
      // Eventuali errori verranno gestiti dal chiamante (il componente).
      try {
        await courseService.exportUdas(courseId, format); // Chiama la nuova funzione del servizio
        // Il download del file è gestito dal browser tramite il servizio.
      } catch (err) {
        console.error(`[courseStore] Failed to trigger ${format.toUpperCase()} export for course ${courseId}:`, err);
        throw err; // Rilancia l'errore in modo che il componente possa gestirlo
      }
    }
  },
  getters: {
    getCourseById: (state) => (id: number) => {
      return state.courses.find(course => course.id === id);
    },
    // Altri getters utili, es. udasForCurrentCourse
    udasForCurrentCourse: (state): UDA[] => {
        return state.currentCourse?.udas || [];
    }
  },
});