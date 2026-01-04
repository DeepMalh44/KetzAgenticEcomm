import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Text } from '@fluentui/react-components';
import RulesList from './pages/Rules/RulesList';
import RuleEditor from './pages/Rules/RuleEditor';
import RulePreview from './pages/Rules/RulePreview';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <nav className="bg-white shadow-sm border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex">
                <div className="flex-shrink-0 flex items-center">
                  <Text size={600} weight="semibold" className="text-blue-600">
                    Merchandising Portal
                  </Text>
                </div>
                <div className="ml-6 flex space-x-8">
                  <Link 
                    to="/" 
                    className="inline-flex items-center px-1 pt-1 text-sm font-medium text-gray-900 hover:text-blue-600"
                  >
                    Rules
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </nav>
        
        <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <Routes>
            <Route path="/" element={<RulesList />} />
            <Route path="/rules/new" element={<RuleEditor />} />
            <Route path="/rules/:id" element={<RuleEditor />} />
            <Route path="/rules/:id/preview" element={<RulePreview />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
