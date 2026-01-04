import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Button,
  Input,
  Textarea,
  Text,
  Field,
  Spinner
} from '@fluentui/react-components';
import { ArrowLeft24Regular, Save24Regular } from '@fluentui/react-icons';
import RuleBuilder from '../../components/RuleBuilder';

const API_BASE = (import.meta as any).env?.VITE_API_BASE || 'http://localhost:8001';

interface RuleFormData {
  name: string;
  description: string;
  priority: number;
  conditions: any;
  actions: any;
}

export default function RuleEditor() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(!!id);
  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState<RuleFormData>({
    name: '',
    description: '',
    priority: 100,
    conditions: { query_contains: [] },
    actions: { action_type: 'boost', products: [], boost_factor: 2.0 }
  });

  useEffect(() => {
    if (id) {
      fetchRule();
    }
  }, [id]);

  const fetchRule = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/rules/${id}`);
      const rule = await response.json();
      setFormData({
        name: rule.name,
        description: rule.description,
        priority: rule.priority,
        conditions: rule.conditions,
        actions: rule.actions
      });
    } catch (error) {
      console.error('Failed to fetch rule:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const url = id ? `${API_BASE}/api/rules/${id}` : `${API_BASE}/api/rules`;
      const method = id ? 'PATCH' : 'POST';
      
      await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      
      navigate('/');
    } catch (error) {
      console.error('Failed to save rule:', error);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Spinner size="large" label="Loading rule..." />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button
          appearance="subtle"
          icon={<ArrowLeft24Regular />}
          onClick={() => navigate('/')}
        />
        <div>
          <Text size={800} weight="semibold">
            {id ? 'Edit Rule' : 'Create New Rule'}
          </Text>
        </div>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-6">
        <Field label="Rule Name" required>
          <Input
            value={formData.name}
            onChange={(_, data) => setFormData({ ...formData, name: data.value })}
            placeholder="e.g., Boost featured products for 'water filter'"
          />
        </Field>

        <Field label="Description">
          <Textarea
            value={formData.description}
            onChange={(_, data) => setFormData({ ...formData, description: data.value })}
            placeholder="What does this rule do?"
            rows={3}
          />
        </Field>

        <Field label="Priority" hint="Higher priority rules are applied first">
          <Input
            type="number"
            value={formData.priority.toString()}
            onChange={(_, data) => setFormData({ ...formData, priority: parseInt(data.value) || 100 })}
          />
        </Field>

        <RuleBuilder
          conditions={formData.conditions}
          actions={formData.actions}
          onConditionsChange={(conditions) => setFormData({ ...formData, conditions })}
          onActionsChange={(actions) => setFormData({ ...formData, actions })}
        />

        <div className="flex justify-end gap-3 pt-4 border-t">
          <Button appearance="secondary" onClick={() => navigate('/')}>
            Cancel
          </Button>
          <Button
            appearance="primary"
            icon={<Save24Regular />}
            onClick={handleSave}
            disabled={saving || !formData.name}
          >
            {saving ? 'Saving...' : 'Save Rule'}
          </Button>
        </div>
      </div>
    </div>
  );
}
