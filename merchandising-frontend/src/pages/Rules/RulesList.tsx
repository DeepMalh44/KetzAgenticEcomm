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
  DialogContent
} from '@fluentui/react-components';
import { Add24Regular, Delete24Regular, Edit24Regular, Eye24Regular } from '@fluentui/react-icons';

interface MerchandisingRule {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
  priority: number;
  conditions: any;
  actions: any;
  created_at: string;
  updated_at: string;
}

const API_BASE = (import.meta as any).env?.VITE_API_BASE || 'https://merchandising-backend.happyisland-58d32b38.eastus2.azurecontainerapps.io';

export default function RulesList() {
  const [rules, setRules] = useState<MerchandisingRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [ruleToDelete, setRuleToDelete] = useState<string | null>(null);
  const navigate = useNavigate();

  const fetchRules = async () => {
    try {
      console.log('Fetching rules from:', `${API_BASE}/api/rules`);
      const response = await fetch(`${API_BASE}/api/rules`);
      console.log('Rules response status:', response.status);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Failed to fetch rules:', errorText);
        setRules([]);
        return;
      }
      
      const data = await response.json();
      console.log('Rules data:', data);
      
      // Handle both array and object responses
      if (Array.isArray(data)) {
        setRules(data);
      } else if (data.rules && Array.isArray(data.rules)) {
        setRules(data.rules);
      } else {
        console.error('Unexpected response format:', data);
        setRules([]);
      }
    } catch (error) {
      console.error('Failed to fetch rules:', error);
      setRules([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRules();
  }, []);

  const handleToggle = async (ruleId: string, enabled: boolean) => {
    try {
      await fetch(`${API_BASE}/api/rules/${ruleId}/toggle`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled })
      });
      await fetchRules();
    } catch (error) {
      console.error('Failed to toggle rule:', error);
    }
  };

  const handleDelete = async () => {
    if (!ruleToDelete) return;
    
    try {
      await fetch(`${API_BASE}/api/rules/${ruleToDelete}`, {
        method: 'DELETE'
      });
      setDeleteDialogOpen(false);
      setRuleToDelete(null);
      await fetchRules();
    } catch (error) {
      console.error('Failed to delete rule:', error);
    }
  };

  const openDeleteDialog = (ruleId: string) => {
    setRuleToDelete(ruleId);
    setDeleteDialogOpen(true);
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Spinner size="large" label="Loading rules..." />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <Text size={800} weight="semibold">Merchandising Rules</Text>
          <Text size={300} className="text-gray-600 block mt-1">
            Manage product boosting, pinning, and burying rules
          </Text>
        </div>
        <Button 
          appearance="primary" 
          icon={<Add24Regular />}
          onClick={() => navigate('/rules/new')}
        >
          Create Rule
        </Button>
      </div>

      {rules.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
          <Text size={500} className="text-gray-500">No rules created yet</Text>
          <Button 
            appearance="primary" 
            className="mt-4"
            icon={<Add24Regular />}
            onClick={() => navigate('/rules/new')}
          >
            Create Your First Rule
          </Button>
        </div>
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHeaderCell>Name</TableHeaderCell>
                <TableHeaderCell>Description</TableHeaderCell>
                <TableHeaderCell>Priority</TableHeaderCell>
                <TableHeaderCell>Status</TableHeaderCell>
                <TableHeaderCell>Actions</TableHeaderCell>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rules.map((rule) => (
                <TableRow key={rule.id}>
                  <TableCell>
                    <Text weight="semibold">{rule.name}</Text>
                  </TableCell>
                  <TableCell>
                    <Text size={300} className="text-gray-600">{rule.description}</Text>
                  </TableCell>
                  <TableCell>
                    <Badge appearance="outline">{rule.priority}</Badge>
                  </TableCell>
                  <TableCell>
                    <Switch
                      checked={rule.enabled}
                      onChange={(_, data) => handleToggle(rule.id, data.checked)}
                    />
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-2">
                      <Button
                        appearance="subtle"
                        icon={<Edit24Regular />}
                        onClick={() => navigate(`/rules/${rule.id}`)}
                      />
                      <Button
                        appearance="subtle"
                        icon={<Eye24Regular />}
                        onClick={() => navigate(`/rules/${rule.id}/preview`)}
                      />
                      <Button
                        appearance="subtle"
                        icon={<Delete24Regular />}
                        onClick={() => openDeleteDialog(rule.id)}
                      />
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      <Dialog open={deleteDialogOpen} onOpenChange={(_, data) => setDeleteDialogOpen(data.open)}>
        <DialogSurface>
          <DialogBody>
            <DialogTitle>Delete Rule</DialogTitle>
            <DialogContent>
              Are you sure you want to delete this rule? This action cannot be undone.
            </DialogContent>
            <DialogActions>
              <DialogTrigger disableButtonEnhancement>
                <Button appearance="secondary">Cancel</Button>
              </DialogTrigger>
              <Button appearance="primary" onClick={handleDelete}>Delete</Button>
            </DialogActions>
          </DialogBody>
        </DialogSurface>
      </Dialog>
    </div>
  );
}
