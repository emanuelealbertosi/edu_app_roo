import AppRoutes from './router'; // Import the routes configuration
import Header from './components/layout/Header'; // Import Header
import Footer from './components/layout/Footer'; // Import Footer

function App() {
  return (
    <div className="flex flex-col min-h-screen"> {/* Use flex to push footer down */}
      <Header />
      <main className="flex-grow container mx-auto px-4 py-8"> {/* Main content area */}
        <AppRoutes /> {/* Render the routes */}
      </main>
      <Footer />
    </div>
  );
}

export default App;
