import { useState, useRef } from 'react';
import {
  Button,
  Text,
  Card,
  Spinner,
  Toast,
  ToastTitle,
  useToastController,
  useId,
  Switch
} from '@fluentui/react-components';
import { ArrowUpload24Regular, DocumentText24Regular } from '@fluentui/react-icons';

const API_BASE = (import.meta as any).env?.VITE_API_BASE || 'https://merchandising-backend.happyisland-58d32b38.eastus2.azurecontainerapps.io';

interface BulkImportResult {
  success: boolean;
  created: number;
  errors: string[];
}

export default function BulkImporter() {
  const [uploading, setUploading] = useState(false);
  const [overwriteExisting, setOverwriteExisting] = useState(false);
  const [result, setResult] = useState<BulkImportResult | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const toasterId = useId('toaster');
  const { dispatchToast } = useToastController(toasterId);

  const handleFileSelect = () => {
    fileInputRef.current?.click();
  };

  const parseCSV = (text: string): any[] => {
    const lines = text.trim().split('\n');
    if (lines.length < 2) {
      throw new Error('CSV must contain header and at least one data row');
    }

    const synonyms = [];
    
    // Skip header row, process data rows
    for (let i = 1; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line) continue;

      // Simple CSV parsing (doesn't handle quoted commas)
      const parts = line.split(',').map(p => p.trim());
      
      if (parts.length < 3) {
        throw new Error(`Invalid row ${i + 1}: must have name, base_term, and at least one synonym`);
      }

      const [name, base_term, ...synonymTerms] = parts;
      
      synonyms.push({
        name,
        base_term: base_term.toLowerCase(),
        synonyms: synonymTerms.filter(s => s).map(s => s.toLowerCase()),
        enabled: true,
        createdBy: 'bulk-import'
      });
    }

    return synonyms;
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.csv')) {
      dispatchToast(
        <Toast>
          <ToastTitle>Invalid file type. Please upload a CSV file.</ToastTitle>
        </Toast>,
        { intent: 'error' }
      );
      return;
    }

    setUploading(true);
    setResult(null);

    try {
      const text = await file.text();
      const synonyms = parseCSV(text);

      const response = await fetch(`${API_BASE}/api/synonyms/bulk-import`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          synonyms,
          overwrite_existing: overwriteExisting
        })
      });

      if (!response.ok) {
        const error = await response.text();
        throw new Error(error);
      }

      const data = await response.json();
      setResult(data);

      dispatchToast(
        <Toast>
          <ToastTitle>Successfully imported {data.created} synonym(s)</ToastTitle>
        </Toast>,
        { intent: 'success' }
      );
    } catch (error: any) {
      console.error('Failed to import synonyms:', error);
      dispatchToast(
        <Toast>
          <ToastTitle>{error.message || 'Failed to import synonyms'}</ToastTitle>
        </Toast>,
        { intent: 'error' }
      );
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const downloadTemplate = () => {
    const template = `name,base_term,synonym1,synonym2,synonym3
Faucet Alternatives,faucet,tap,spigot,valve
Refrigerator Terms,refrigerator,fridge,icebox,cooler
Couch Synonyms,couch,sofa,settee,divan`;

    const blob = new Blob([template], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'synonyms-template.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Card>
      <div className="p-4 space-y-4">
        <div>
          <Text size={500} weight="semibold">Bulk Import Synonyms</Text>
          <p className="mt-1 text-sm text-gray-500">
            Upload a CSV file to import multiple synonym groups at once
          </p>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
          <Text size={300} weight="semibold" className="mb-2 block">
            CSV Format:
          </Text>
          <p className="text-sm text-gray-700 mb-2">
            Your CSV should have the following format:
          </p>
          <pre className="text-xs bg-white p-2 rounded border border-blue-300 overflow-x-auto">
            name,base_term,synonym1,synonym2,synonym3{'\n'}
            Faucet Alternatives,faucet,tap,spigot,valve{'\n'}
            Refrigerator Terms,refrigerator,fridge,icebox
          </pre>
          <p className="text-xs text-gray-600 mt-2">
            • First row must be headers{'\n'}
            • Each row: name, base_term, and any number of synonyms{'\n'}
            • All terms will be converted to lowercase
          </p>
        </div>

        <div className="flex items-center gap-4">
          <Button
            appearance="secondary"
            icon={<DocumentText24Regular />}
            onClick={downloadTemplate}
          >
            Download Template
          </Button>
          
          <Switch
            checked={overwriteExisting}
            onChange={(e) => setOverwriteExisting(e.currentTarget.checked)}
            label="Overwrite existing synonyms"
          />
        </div>

        <input
          ref={fileInputRef}
          type="file"
          accept=".csv"
          onChange={handleFileUpload}
          style={{ display: 'none' }}
        />

        <Button
          appearance="primary"
          icon={<ArrowUpload24Regular />}
          onClick={handleFileSelect}
          disabled={uploading}
          size="large"
        >
          {uploading ? 'Uploading...' : 'Upload CSV'}
        </Button>

        {uploading && (
          <div className="flex items-center justify-center py-8">
            <Spinner label="Importing synonyms..." />
          </div>
        )}

        {result && !uploading && (
          <div className="space-y-2">
            {result.success && (
              <div className="bg-green-50 border border-green-200 rounded-md p-4">
                <Text size={300} weight="semibold" className="text-green-800">
                  ✅ Import Successful
                </Text>
                <p className="text-sm text-green-700 mt-1">
                  Created {result.created} synonym group(s)
                </p>
              </div>
            )}

            {result.errors.length > 0 && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
                <Text size={300} weight="semibold" className="text-yellow-800">
                  ⚠️ Some Errors Occurred:
                </Text>
                <ul className="text-sm text-yellow-700 mt-2 list-disc list-inside">
                  {result.errors.map((error, idx) => (
                    <li key={idx}>{error}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </Card>
  );
}
