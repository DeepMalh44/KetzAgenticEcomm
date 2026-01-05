import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Button,
  Input,
  Label,
  Text,
  Spinner,
  Card,
  Badge,
  Toast,
  ToastTitle,
  useToastController,
  Toaster,
  useId,
  Switch
} from '@fluentui/react-components';
import { Add24Regular, Dismiss24Regular, Save24Regular, ArrowLeft24Regular } from '@fluentui/react-icons';

interface SynonymGroup {
  id?: string;
  name: string;
  base_term: string;
  synonyms: string[];
  enabled: boolean;
  createdBy: string;
}

const API_BASE = (import.meta as any).env?.VITE_API_BASE || 'https://merchandising-backend.happyisland-58d32b38.eastus2.azurecontainerapps.io';

export default function SynonymEditor() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const isEditMode = !!id;

  const [loading, setLoading] = useState(isEditMode);
  const [saving, setSaving] = useState(false);
  
  const [name, setName] = useState('');
  const [baseTerm, setBaseTerm] = useState('');
  const [synonyms, setSynonyms] = useState<string[]>([]);
  const [newSynonym, setNewSynonym] = useState('');
  const [enabled, setEnabled] = useState(true);
  
  const toasterId = useId('toaster');
  const { dispatchToast } = useToastController(toasterId);

  useEffect(() => {
    if (isEditMode && id) {
      fetchSynonym(id);
    }
  }, [id, isEditMode]);

  const fetchSynonym = async (synonymId: string) => {
    try {
      const response = await fetch(`${API_BASE}/api/synonyms/${synonymId}`);
      
      if (!response.ok) throw new Error('Failed to fetch synonym');
      
      const data = await response.json();
      setName(data.name);
      setBaseTerm(data.base_term);
      setSynonyms(data.synonyms || []);
      setEnabled(data.enabled);
    } catch (error) {
      console.error('Failed to fetch synonym:', error);
      dispatchToast(
        <Toast>
          <ToastTitle>Failed to load synonym</ToastTitle>
        </Toast>,
        { intent: 'error' }
      );
      navigate('/synonyms');
    } finally {
      setLoading(false);
    }
  };

  const handleAddSynonym = () => {
    const trimmed = newSynonym.trim();
    if (trimmed) {
      setSynonyms(prevSynonyms => {
        if (prevSynonyms.includes(trimmed)) {
          dispatchToast(
            <Toast>
              <ToastTitle>Synonym already added</ToastTitle>
            </Toast>,
            { intent: 'info' }
          );
          return prevSynonyms;
        }
        return [...prevSynonyms, trimmed];
      });
      setNewSynonym('');
    }
  };

  const handleRemoveSynonym = (index: number) => {
    setSynonyms(synonyms.filter((_, i) => i !== index));
  };

  const handleSave = async () => {
    // Validation
    if (!name.trim()) {
      dispatchToast(
        <Toast>
          <ToastTitle>Name is required</ToastTitle>
        </Toast>,
        { intent: 'warning' }
      );
      return;
    }

    if (!baseTerm.trim()) {
      dispatchToast(
        <Toast>
          <ToastTitle>Base term is required</ToastTitle>
        </Toast>,
        { intent: 'warning' }
      );
      return;
    }

    if (synonyms.length === 0) {
      dispatchToast(
        <Toast>
          <ToastTitle>Add at least one synonym</ToastTitle>
        </Toast>,
        { intent: 'warning' }
      );
      return;
    }

    setSaving(true);

    try {
      const synonymData: SynonymGroup = {
        name: name.trim(),
        base_term: baseTerm.trim().toLowerCase(),
        synonyms: synonyms.map(s => s.trim().toLowerCase()),
        enabled,
        createdBy: 'user'
      };

      const url = isEditMode 
        ? `${API_BASE}/api/synonyms/${id}`
        : `${API_BASE}/api/synonyms`;
      
      const method = isEditMode ? 'PATCH' : 'POST';

      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(synonymData)
      });

      if (!response.ok) {
        const error = await response.text();
        throw new Error(error);
      }

      dispatchToast(
        <Toast>
          <ToastTitle>Synonym {isEditMode ? 'updated' : 'created'} successfully and synced to Azure AI Search</ToastTitle>
        </Toast>,
        { intent: 'success' }
      );

      navigate('/synonyms');
    } catch (error) {
      console.error('Failed to save synonym:', error);
      dispatchToast(
        <Toast>
          <ToastTitle>Failed to save synonym</ToastTitle>
        </Toast>,
        { intent: 'error' }
      );
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spinner label="Loading synonym..." />
      </div>
    );
  }

  return (
    <>
      <Toaster toasterId={toasterId} />
      
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="mb-6">
          <Button
            appearance="subtle"
            icon={<ArrowLeft24Regular />}
            onClick={() => navigate('/synonyms')}
          >
            Back to Synonyms
          </Button>
        </div>

        <div className="sm:flex sm:items-center mb-6">
          <div className="sm:flex-auto">
            <Text size={900} weight="semibold">
              {isEditMode ? 'Edit Synonym' : 'Create New Synonym'}
            </Text>
            <p className="mt-2 text-sm text-gray-700">
              Define a base term and its synonymous terms. Changes will be synced to Azure AI Search.
            </p>
          </div>
        </div>

        <div className="space-y-6 max-w-3xl">
          <Card>
            <div className="space-y-4 p-4">
              <div>
                <Label htmlFor="name" required>Synonym Group Name</Label>
                <Input
                  id="name"
                  value={name}
                  onChange={(_, data) => setName(data.value)}
                  placeholder="e.g., Faucet Alternatives"
                  className="mt-1"
                />
                <p className="mt-1 text-xs text-gray-500">
                  A descriptive name for this synonym group
                </p>
              </div>

              <div>
                <Label htmlFor="baseTerm" required>Base Term</Label>
                <Input
                  id="baseTerm"
                  value={baseTerm}
                  onChange={(_, data) => setBaseTerm(data.value)}
                  placeholder="e.g., faucet"
                  className="mt-1"
                />
                <p className="mt-1 text-xs text-gray-500">
                  The primary search term (will be converted to lowercase)
                </p>
              </div>

              <div>
                <Label htmlFor="newSynonym" required>Synonyms</Label>
                <div className="flex gap-2 mt-1">
                  <Input
                    id="newSynonym"
                    value={newSynonym}
                    onChange={(_, data) => setNewSynonym(data.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        handleAddSynonym();
                      }
                    }}
                    placeholder="e.g., tap, spigot"
                    className="flex-1"
                  />
                  <Button
                    appearance="secondary"
                    icon={<Add24Regular />}
                    onClick={handleAddSynonym}
                    disabled={!newSynonym.trim()}
                  >
                    Add
                  </Button>
                </div>
                <p className="mt-1 text-xs text-gray-500">
                  Alternative terms that should match the base term (will be converted to lowercase)
                </p>
              </div>

              {synonyms.length > 0 && (
                <div>
                  <Text size={300} weight="semibold" className="mb-2 block">Current Synonyms:</Text>
                  <div className="flex flex-wrap gap-2">
                    {synonyms.map((synonym, index) => (
                      <div key={index} className="inline-flex items-center gap-1 px-3 py-1 bg-blue-100 text-blue-800 rounded-full">
                        <span className="text-sm">{synonym}</span>
                        <button
                          onClick={() => handleRemoveSynonym(index)}
                          className="ml-1 hover:bg-blue-200 rounded-full p-0.5"
                          aria-label="Remove"
                        >
                          <Dismiss24Regular className="w-4 h-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div>
                <Switch
                  checked={enabled}
                  onChange={(e) => setEnabled(e.currentTarget.checked)}
                  label={enabled ? 'Enabled' : 'Disabled'}
                />
                <p className="mt-1 text-xs text-gray-500">
                  Only enabled synonyms are synced to Azure AI Search
                </p>
              </div>
            </div>
          </Card>

          <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
            <Text size={300} weight="semibold" className="mb-2 block">Preview:</Text>
            <p className="text-sm text-gray-700">
              When users search for <Badge appearance="outline">{baseTerm || 'base_term'}</Badge>, results will also include items matching:
            </p>
            <div className="flex flex-wrap gap-2 mt-2">
              {synonyms.map((synonym, idx) => (
                <Badge key={idx} appearance="tint">{synonym}</Badge>
              ))}
            </div>
            <p className="text-xs text-gray-500 mt-2">
              This works bidirectionally - searching for any synonym will also match the base term
            </p>
          </div>

          <div className="flex justify-end gap-3">
            <Button
              appearance="secondary"
              onClick={() => navigate('/synonyms')}
            >
              Cancel
            </Button>
            <Button
              appearance="primary"
              icon={<Save24Regular />}
              onClick={handleSave}
              disabled={saving || synonyms.length === 0}
            >
              {saving ? 'Saving...' : (isEditMode ? 'Update' : 'Create')} & Sync
            </Button>
          </div>
        </div>
      </div>
    </>
  );
}
