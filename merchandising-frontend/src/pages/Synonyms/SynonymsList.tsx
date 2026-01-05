import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Button,
  Table,
  TableBody,
  TableCell,
  TableRow,
  TableHeader,
  TableHeaderCell,
  Text,
  Badge,
  Switch,
  Spinner,
  Dialog,
  DialogTrigger,
  DialogSurface,
  DialogTitle,
  DialogBody,
  DialogActions,
  DialogContent,
  Toast,
  ToastTitle,
  useToastController,
  Toaster,
  useId
} from '@fluentui/react-components';
import { Add24Regular, Delete24Regular, Edit24Regular, ArrowSync24Regular } from '@fluentui/react-icons';

interface SynonymGroup {
  id: string;
  name: string;
  base_term: string;
  synonyms: string[];
  enabled: boolean;
  createdBy: string;
  createdAt: string;
}

const API_BASE = (import.meta as any).env?.VITE_API_BASE || 'https://merchandising-backend.happyisland-58d32b38.eastus2.azurecontainerapps.io';

export default function SynonymsList() {
  const [synonyms, setSynonyms] = useState<SynonymGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [synonymToDelete, setSynonymToDelete] = useState<string | null>(null);
  const navigate = useNavigate();
  
  const toasterId = useId('toaster');
  const { dispatchToast } = useToastController(toasterId);

  const fetchSynonyms = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/synonyms`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch synonyms');
      }
      
      const data = await response.json();
      
      if (Array.isArray(data)) {
        setSynonyms(data);
      } else if (data.synonyms && Array.isArray(data.synonyms)) {
        setSynonyms(data.synonyms);
      } else {
        setSynonyms([]);
      }
    } catch (error) {
      console.error('Failed to fetch synonyms:', error);
      setSynonyms([]);
      dispatchToast(
        <Toast>
          <ToastTitle>Failed to load synonyms</ToastTitle>
        </Toast>,
        { intent: 'error' }
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSynonyms();
  }, []);

  const handleToggle = async (synonymId: string) => {
    try {
      const response = await fetch(`${API_BASE}/api/synonyms/${synonymId}/toggle`, {
        method: 'POST'
      });
      
      if (!response.ok) throw new Error('Failed to toggle synonym');
      
      await fetchSynonyms();
      dispatchToast(
        <Toast>
          <ToastTitle>Synonym updated successfully</ToastTitle>
        </Toast>,
        { intent: 'success' }
      );
    } catch (error) {
      console.error('Failed to toggle synonym:', error);
      dispatchToast(
        <Toast>
          <ToastTitle>Failed to update synonym</ToastTitle>
        </Toast>,
        { intent: 'error' }
      );
    }
  };

  const handleSync = async () => {
    setSyncing(true);
    try {
      const response = await fetch(`${API_BASE}/api/synonyms/sync`, {
        method: 'POST'
      });
      
      if (!response.ok) throw new Error('Failed to sync synonyms');
      
      const data = await response.json();
      dispatchToast(
        <Toast>
          <ToastTitle>{data.message}</ToastTitle>
        </Toast>,
        { intent: 'success' }
      );
    } catch (error) {
      console.error('Failed to sync synonyms:', error);
      dispatchToast(
        <Toast>
          <ToastTitle>Failed to sync with Azure AI Search</ToastTitle>
        </Toast>,
        { intent: 'error' }
      );
    } finally {
      setSyncing(false);
    }
  };

  const handleDelete = async () => {
    if (!synonymToDelete) return;
    
    try {
      const response = await fetch(`${API_BASE}/api/synonyms/${synonymToDelete}`, {
        method: 'DELETE'
      });
      
      if (!response.ok) throw new Error('Failed to delete synonym');
      
      await fetchSynonyms();
      dispatchToast(
        <Toast>
          <ToastTitle>Synonym deleted successfully</ToastTitle>
        </Toast>,
        { intent: 'success' }
      );
    } catch (error) {
      console.error('Failed to delete synonym:', error);
      dispatchToast(
        <Toast>
          <ToastTitle>Failed to delete synonym</ToastTitle>
        </Toast>,
        { intent: 'error' }
      );
    } finally {
      setDeleteDialogOpen(false);
      setSynonymToDelete(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spinner label="Loading synonyms..." />
      </div>
    );
  }

  return (
    <>
      <Toaster toasterId={toasterId} />
      
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="sm:flex sm:items-center">
          <div className="sm:flex-auto">
            <Text size={900} weight="semibold">Synonyms</Text>
            <p className="mt-2 text-sm text-gray-700">
              Manage search synonyms that expand queries in Azure AI Search
            </p>
          </div>
          <div className="mt-4 sm:mt-0 sm:ml-16 sm:flex-none flex gap-2">
            <Button
              appearance="secondary"
              icon={<ArrowSync24Regular />}
              onClick={handleSync}
              disabled={syncing}
            >
              {syncing ? 'Syncing...' : 'Sync to Azure'}
            </Button>
            <Button
              appearance="primary"
              icon={<Add24Regular />}
              onClick={() => navigate('/synonyms/new')}
            >
              Add Synonym
            </Button>
          </div>
        </div>

        <div className="mt-8 flow-root">
          {synonyms.length === 0 ? (
            <div className="text-center py-12">
              <Text size={600}>No synonyms found</Text>
              <p className="mt-2 text-sm text-gray-500">
                Get started by creating your first synonym group
              </p>
              <Button
                appearance="primary"
                icon={<Add24Regular />}
                onClick={() => navigate('/synonyms/new')}
                className="mt-4"
              >
                Add Synonym
              </Button>
            </div>
          ) : (
            <div className="-mx-4 -my-2 overflow-x-auto sm:-mx-6 lg:-mx-8">
              <div className="inline-block min-w-full py-2 align-middle sm:px-6 lg:px-8">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHeaderCell>Name</TableHeaderCell>
                      <TableHeaderCell>Base Term</TableHeaderCell>
                      <TableHeaderCell>Synonyms</TableHeaderCell>
                      <TableHeaderCell>Status</TableHeaderCell>
                      <TableHeaderCell>Actions</TableHeaderCell>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {synonyms.map((synonym) => (
                      <TableRow key={synonym.id}>
                        <TableCell>
                          <Text weight="semibold">{synonym.name}</Text>
                        </TableCell>
                        <TableCell>
                          <Badge appearance="outline">{synonym.base_term}</Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex flex-wrap gap-1">
                            {synonym.synonyms.map((term, idx) => (
                              <Badge key={idx} appearance="tint">{term}</Badge>
                            ))}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Switch
                            checked={synonym.enabled}
                            onChange={() => handleToggle(synonym.id)}
                            label={synonym.enabled ? 'Enabled' : 'Disabled'}
                          />
                        </TableCell>
                        <TableCell>
                          <div className="flex gap-2">
                            <Button
                              appearance="subtle"
                              icon={<Edit24Regular />}
                              onClick={() => navigate(`/synonyms/${synonym.id}`)}
                            />
                            <Button
                              appearance="subtle"
                              icon={<Delete24Regular />}
                              onClick={() => {
                                setSynonymToDelete(synonym.id);
                                setDeleteDialogOpen(true);
                              }}
                            />
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </div>
          )}
        </div>

        <Dialog open={deleteDialogOpen} onOpenChange={(_, data) => setDeleteDialogOpen(data.open)}>
          <DialogSurface>
            <DialogBody>
              <DialogTitle>Delete Synonym</DialogTitle>
              <DialogContent>
                Are you sure you want to delete this synonym? This will also sync changes to Azure AI Search.
              </DialogContent>
              <DialogActions>
                <DialogTrigger disableButtonEnhancement>
                  <Button appearance="secondary">Cancel</Button>
                </DialogTrigger>
                <Button appearance="primary" onClick={handleDelete}>
                  Delete
                </Button>
              </DialogActions>
            </DialogBody>
          </DialogSurface>
        </Dialog>
      </div>
    </>
  );
}
