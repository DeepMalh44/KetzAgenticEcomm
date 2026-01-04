import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Button,
  Input,
  Text,
  Spinner,
  Card,
  Badge
} from '@fluentui/react-components';
import { ArrowLeft24Regular, Search24Regular } from '@fluentui/react-icons';

const API_BASE = (import.meta as any).env?.VITE_API_BASE || 'http://localhost:8001';

interface PreviewResult {
  id: string;
  name: string;
  category: string;
  price: number;
  originalScore?: number;
  newScore?: number;
  position?: number;
  action?: string;
}

export default function RulePreview() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<PreviewResult[]>([]);
  const [rule, setRule] = useState<any>(null);

  useEffect(() => {
    if (id) {
      fetchRule();
    }
  }, [id]);

  const fetchRule = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/rules/${id}`);
      const data = await response.json();
      setRule(data);
    } catch (error) {
      console.error('Failed to fetch rule:', error);
    }
  };

  const handlePreview = async () => {
    if (!query) return;
    
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/rules/${id}/preview`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      });
      const data = await response.json();
      setResults(data.results || []);
    } catch (error) {
      console.error('Failed to preview rule:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button
          appearance="subtle"
          icon={<ArrowLeft24Regular />}
          onClick={() => navigate('/')}
        />
        <div>
          <Text size={800} weight="semibold">Preview Rule</Text>
          {rule && (
            <Text size={300} className="text-gray-600 block mt-1">
              {rule.name}
            </Text>
          )}
        </div>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex gap-3">
          <Input
            className="flex-1"
            value={query}
            onChange={(_, data) => setQuery(data.value)}
            placeholder="Enter a search query to preview rule effects..."
            onKeyPress={(e) => e.key === 'Enter' && handlePreview()}
          />
          <Button
            appearance="primary"
            icon={<Search24Regular />}
            onClick={handlePreview}
            disabled={!query || loading}
          >
            Preview
          </Button>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center items-center h-64">
          <Spinner size="large" label="Generating preview..." />
        </div>
      ) : results.length > 0 ? (
        <div className="space-y-4">
          <Text size={600} weight="semibold">
            Preview Results ({results.length} products)
          </Text>
          <div className="grid gap-4">
            {results.map((result, index) => (
              <Card key={result.id} className="p-4">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <Text weight="semibold">{index + 1}. {result.name}</Text>
                      {result.action && (
                        <Badge appearance="filled" color={
                          result.action === 'pinned' ? 'brand' :
                          result.action === 'boosted' ? 'success' :
                          'danger'
                        }>
                          {result.action}
                        </Badge>
                      )}
                    </div>
                    <Text size={300} className="text-gray-600 mt-1">
                      {result.category}
                    </Text>
                  </div>
                  <div className="text-right">
                    <Text weight="semibold">${result.price.toFixed(2)}</Text>
                    {result.originalScore !== undefined && (
                      <Text size={200} className="text-gray-500 block mt-1">
                        Score: {result.originalScore.toFixed(2)} → {result.newScore?.toFixed(2)}
                      </Text>
                    )}
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      ) : query && !loading ? (
        <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
          <Text size={500} className="text-gray-500">No results found</Text>
        </div>
      ) : null}
    </div>
  );
}
