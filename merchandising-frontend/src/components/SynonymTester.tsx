import { useState } from 'react';
import {
  Button,
  Input,
  Label,
  Text,
  Card,
  Spinner,
  Badge,
  Toast,
  ToastTitle,
  useToastController,
  useId
} from '@fluentui/react-components';
import { Search24Regular } from '@fluentui/react-icons';

const API_BASE = (import.meta as any).env?.VITE_API_BASE || 'https://merchandising-backend.happyisland-58d32b38.eastus2.azurecontainerapps.io';

interface TestResult {
  query: string;
  expanded_terms: string[];
  sample_results: any[];
}

export default function SynonymTester() {
  const [query, setQuery] = useState('');
  const [testing, setTesting] = useState(false);
  const [result, setResult] = useState<TestResult | null>(null);
  
  const toasterId = useId('toaster');
  const { dispatchToast } = useToastController(toasterId);

  const handleTest = async () => {
    if (!query.trim()) {
      dispatchToast(
        <Toast>
          <ToastTitle>Enter a search query to test</ToastTitle>
        </Toast>,
        { intent: 'warning' }
      );
      return;
    }

    setTesting(true);
    try {
      const response = await fetch(`${API_BASE}/api/synonyms/test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query.trim() })
      });

      if (!response.ok) throw new Error('Failed to test synonym');

      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Failed to test synonym:', error);
      dispatchToast(
        <Toast>
          <ToastTitle>Failed to test synonym</ToastTitle>
        </Toast>,
        { intent: 'error' }
      );
    } finally {
      setTesting(false);
    }
  };

  return (
    <Card>
      <div className="p-4 space-y-4">
        <div>
          <Text size={500} weight="semibold">Test Synonym Expansion</Text>
          <p className="mt-1 text-sm text-gray-500">
            Test how search queries are expanded with current synonyms
          </p>
        </div>

        <div>
          <Label htmlFor="testQuery">Search Query</Label>
          <div className="flex gap-2 mt-1">
            <Input
              id="testQuery"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  handleTest();
                }
              }}
              placeholder="e.g., faucet"
              className="flex-1"
            />
            <Button
              appearance="primary"
              icon={<Search24Regular />}
              onClick={handleTest}
              disabled={testing}
            >
              {testing ? 'Testing...' : 'Test'}
            </Button>
          </div>
        </div>

        {testing && (
          <div className="flex items-center justify-center py-8">
            <Spinner label="Testing synonym expansion..." />
          </div>
        )}

        {result && !testing && (
          <div className="space-y-4">
            <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
              <Text size={300} weight="semibold" className="mb-2 block">
                Query Expansion:
              </Text>
              <p className="text-sm text-gray-700 mb-2">
                Original: <Badge appearance="outline">{result.query}</Badge>
              </p>
              {result.expanded_terms.length > 1 ? (
                <div>
                  <p className="text-sm text-gray-700 mb-2">Expanded to include:</p>
                  <div className="flex flex-wrap gap-2">
                    {result.expanded_terms.map((term, idx) => (
                      <Badge key={idx} appearance="tint">{term}</Badge>
                    ))}
                  </div>
                </div>
              ) : (
                <p className="text-sm text-gray-500">
                  No synonym expansion available for this query
                </p>
              )}
            </div>

            {result.sample_results.length > 0 && (
              <div>
                <Text size={300} weight="semibold" className="mb-2 block">
                  Sample Results:
                </Text>
                <div className="space-y-2">
                  {result.sample_results.map((product, idx) => (
                    <div key={idx} className="border border-gray-200 rounded-md p-3">
                      <Text weight="semibold">{product.name}</Text>
                      <p className="text-sm text-gray-500">{product.category}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </Card>
  );
}
