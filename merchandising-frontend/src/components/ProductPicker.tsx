import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogSurface,
  DialogTitle,
  DialogBody,
  DialogActions,
  DialogContent,
  Button,
  Input,
  Spinner,
  Checkbox,
  Text
} from '@fluentui/react-components';
import { Search24Regular, Dismiss24Regular } from '@fluentui/react-icons';

interface ProductPickerProps {
  selectedProducts: string[];
  onSelect: (productIds: string[]) => void;
  onClose: () => void;
}

interface Product {
  id: string;
  name: string;
  category: string;
  price: number;
}

// Call backend directly - Azure Container Apps are separate
const BACKEND_URL = (import.meta as any).env?.VITE_BACKEND_URL || 'https://merchandising-backend.happyisland-58d32b38.eastus2.azurecontainerapps.io';
const SEARCH_API = `${BACKEND_URL}/api/products/search`;

export default function ProductPicker({ selectedProducts, onSelect, onClose }: ProductPickerProps) {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<Product[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set(selectedProducts));

  useEffect(() => {
    if (query && query.length >= 2) {
      const timeoutId = setTimeout(() => {
        searchProducts();
      }, 500); // Debounce 500ms
      
      return () => clearTimeout(timeoutId);
    } else {
      setResults([]);
      setLoading(false);
    }
  }, [query]);

  const searchProducts = async () => {
    setLoading(true);
    try {
      console.log('Searching for:', query);
      console.log('API URL:', SEARCH_API);
      
      const url = `${SEARCH_API}?q=${encodeURIComponent(query)}`;
      console.log('Full URL:', url);
      
      const response = await fetch(url);
      console.log('Response status:', response.status);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('Response data:', data);
      
      setResults(data.results || data.products || []);
    } catch (error) {
      console.error('Failed to search products:', error);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const toggleProduct = (productId: string) => {
    const newSelected = new Set(selected);
    if (newSelected.has(productId)) {
      newSelected.delete(productId);
    } else {
      newSelected.add(productId);
    }
    setSelected(newSelected);
  };

  const handleConfirm = () => {
    onSelect(Array.from(selected));
  };

  return (
    <Dialog open onOpenChange={(_, data) => !data.open && onClose()}>
      <DialogSurface className="max-w-3xl">
        <DialogBody>
          <DialogTitle
            action={
              <Button
                appearance="subtle"
                icon={<Dismiss24Regular />}
                onClick={onClose}
              />
            }
          >
            Select Products
          </DialogTitle>
          <DialogContent>
            <div className="space-y-4">
              <div className="flex gap-2">
                <Input
                  className="flex-1"
                  value={query}
                  onChange={(_, data) => setQuery(data.value)}
                  placeholder="Search for products..."
                  contentBefore={<Search24Regular />}
                />
              </div>

              {loading ? (
                <div className="flex justify-center py-8">
                  <Spinner label="Searching..." />
                </div>
              ) : results.length > 0 ? (
                <div className="max-h-96 overflow-y-auto space-y-2">
                  {results.map((product) => (
                    <div
                      key={product.id}
                      className="flex items-center gap-3 p-3 border rounded hover:bg-gray-50 cursor-pointer"
                      onClick={() => toggleProduct(product.id)}
                    >
                      <Checkbox
                        checked={selected.has(product.id)}
                        onChange={() => toggleProduct(product.id)}
                      />
                      <div className="flex-1">
                        <Text weight="semibold">{product.name}</Text>
                        <Text size={300} className="text-gray-600 block">
                          {product.category} • ${product.price.toFixed(2)}
                        </Text>
                      </div>
                    </div>
                  ))}
                </div>
              ) : query ? (
                <div className="text-center py-8 text-gray-500">
                  <Text>No products found</Text>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <Text>Start typing to search for products</Text>
                </div>
              )}

              {selected.size > 0 && (
                <div className="pt-4 border-t">
                  <Text size={300} className="text-gray-600">
                    {selected.size} product(s) selected
                  </Text>
                </div>
              )}
            </div>
          </DialogContent>
          <DialogActions>
            <Button appearance="secondary" onClick={onClose}>
              Cancel
            </Button>
            <Button
              appearance="primary"
              onClick={handleConfirm}
              disabled={selected.size === 0}
            >
              Confirm Selection
            </Button>
          </DialogActions>
        </DialogBody>
      </DialogSurface>
    </Dialog>
  );
}
