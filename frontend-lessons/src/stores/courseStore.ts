import { defineStore } from 'pinia';
import { courseService } from '@/services/courseService';
import type { Course, UDA, CourseGroup } from '@/types/uda';
import { useUiStore } from './ui';
import axios from 'axios';

interface CourseState {
  courses: Course[];
  courseGroups: CourseGroup[];
  currentCourse: Course | null;
  loading: boolean;
  isLoadingCourseGroups: boolean;
  error: string | null;
}

export const useCourseStore = defineStore('course', {
  state: (): CourseState => ({
    courses: [],
    courseGroups: [],
    currentCourse: null,
    loading: false,
    isLoadingCourseGroups: false,
    error: null,
  }),
  actions: {
    // GROUP ACTIONS
    async fetchCourseGroups() {
      this.isLoadingCourseGroups = true;
      this.error = null;
      try {
        this.courseGroups = await courseService.getCourseGroups();
      } catch (err) {
        this.error = (err as Error).message || 'Failed to fetch course groups';
        this.courseGroups = [];
      } finally {
        this.isLoadingCourseGroups = false;
      }
    },

    async createCourseGroup(name: string): Promise<CourseGroup | undefined> {
      this.isLoadingCourseGroups = true;
      try {
        const newGroup = await courseService.createCourseGroup({ name });
        this.courseGroups.push(newGroup);
        return newGroup;
      } catch (error) {
        this.error = (error as Error).message || 'Failed to create course group';
        throw error;
      } finally {
        this.isLoadingCourseGroups = false;
      }
    },

    async updateCourseGroup(id: number, name: string): Promise<CourseGroup | undefined> {
        this.isLoadingCourseGroups = true;
        try {
            const updatedGroup = await courseService.updateCourseGroup(id, { name });
            const index = this.courseGroups.findIndex(g => g.id === id);
            if (index !== -1) {
                this.courseGroups[index] = updatedGroup;
            }
            // Aggiorna anche i corsi che potrebbero avere questo gruppo
            this.courses.forEach(course => {
                if (course.group?.id === id) {
                    course.group = updatedGroup;
                }
            });
            return updatedGroup;
        } catch (error) {
            this.error = (error as Error).message || 'Failed to update course group';
            throw error;
        } finally {
            this.isLoadingCourseGroups = false;
        }
    },


    async deleteCourseGroup(id: number) {
      this.isLoadingCourseGroups = true;
      try {
        await courseService.deleteCourseGroup(id);
        this.courseGroups = this.courseGroups.filter(g => g.id !== id);
        // Rimuovi il gruppo da tutti i corsi che lo avevano assegnato
        this.courses.forEach(course => {
          if (course.group?.id === id) {
            course.group = null;
            course.group_id = null;
          }
        });
      } catch (error) {
        this.error = (error as Error).message || 'Failed to delete course group';
        throw error;
      } finally {
        this.isLoadingCourseGroups = false;
      }
    },

    async assignCoursesToGroup(courseIds: number[], groupId: number | null) {
        this.loading = true;
        try {
            const group = this.courseGroups.find(g => g.id === groupId) || null;
            // Ottimisticamente, aggiorna il frontend prima della risposta del backend
            this.courses.forEach(course => {
                if (courseIds.includes(course.id)) {
                    course.group = group;
                    course.group_id = groupId;
                }
            });
            // Chiamata al servizio per aggiornare il backend per ogni corso
            // Questo potrebbe essere ottimizzato con un endpoint batch se disponibile
            const updatePromises = courseIds.map(courseId =>
                courseService.updateCourse(courseId, { group_id: groupId })
            );
            await Promise.all(updatePromises);
            // Opzionale: rifare il fetch dei corsi per essere sicuri dello stato
            // await this.fetchCourses();
        } catch (error) {
            this.error = (error as Error).message || 'Failed to assign courses to group';
            // Rollback in caso di errore
            await this.fetchCourses();
            throw error;
        } finally {
            this.loading = false;
        }
    },

    async removeCourseFromGroup(courseId: number) {
        this.loading = true;
        try {
            const course = this.courses.find(c => c.id === courseId);
            if (course) {
                course.group = null;
                course.group_id = null;
            }
            await courseService.updateCourse(courseId, { group_id: null });
        } catch (error) {
            this.error = (error as Error).message || 'Failed to remove course from group';
            await this.fetchCourses(); // Rollback
            throw error;
        } finally {
            this.loading = false;
        }
    },

    async removeCoursesFromGroup(courseIds: number[]) {
        this.loading = true;
        try {
            // Ottimisticamente
            this.courses.forEach(course => {
                if (courseIds.includes(course.id)) {
                    course.group = null;
                    course.group_id = null;
                }
            });
            const updatePromises = courseIds.map(courseId =>
                courseService.updateCourse(courseId, { group_id: null })
            );
            await Promise.all(updatePromises);
        } catch (error) {
            this.error = (error as Error).message || 'Failed to remove courses from group';
            await this.fetchCourses(); // Rollback
            throw error;
        } finally {
            this.loading = false;
        }
    },

    // COURSE ACTIONS
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

    async updateCourse(id: number, courseData: Partial<Pick<Course, 'name' | 'description' | 'group_id'>>): Promise<Course | undefined> {
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
        const uiStore = useUiStore();
        if (axios.isAxiosError(err) && err.response) {
          const errorMessage = err.response.data.error || 'Errore durante la copia del corso.';
          uiStore.addNotification({
            title: 'Errore',
            message: errorMessage,
            type: 'error',
            duration: 5000
          });
        } else {
          uiStore.addNotification({
            title: 'Errore',
            message: 'Si è verificato un errore imprevisto.',
            type: 'error',
            duration: 5000
          });
        }
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