import { useState } from 'react';
import {
  Field,
  Input,
  Button,
  Text,
  TagGroup,
  Tag,
  Select
} from '@fluentui/react-components';
import { Add24Regular, Delete24Regular } from '@fluentui/react-icons';
import ProductPicker from './ProductPicker';

interface RuleBuilderProps {
  conditions: any;
  actions: any;
  onConditionsChange: (conditions: any) => void;
  onActionsChange: (actions: any) => void;
}

export default function RuleBuilder({
  conditions,
  actions,
  onConditionsChange,
  onActionsChange
}: RuleBuilderProps) {
  const [showProductPicker, setShowProductPicker] = useState(false);
  const [queryKeyword, setQueryKeyword] = useState('');

  const addQueryKeyword = () => {
    if (!queryKeyword) return;
    const keywords = conditions.query_contains || [];
    onConditionsChange({
      ...conditions,
      query_contains: [...keywords, queryKeyword]
    });
    setQueryKeyword('');
  };

  const removeQueryKeyword = (keyword: string) => {
    const keywords = conditions.query_contains || [];
    onConditionsChange({
      ...conditions,
      query_contains: keywords.filter((k: string) => k !== keyword)
    });
  };

  const handleProductsSelected = (productIds: string[]) => {
    onActionsChange({
      ...actions,
      products: productIds
    });
    setShowProductPicker(false);
  };

  const removeProduct = (productId: string) => {
    onActionsChange({
      ...actions,
      products: actions.products.filter((p: string) => p !== productId)
    });
  };

  return (
    <div className="space-y-6">
      {/* Conditions Section */}
      <div className="space-y-4">
        <Text size={600} weight="semibold">When (Conditions)</Text>
        
        <Field label="Query Contains Keywords" hint="Rule applies when search query contains any of these">
          <div className="flex gap-2">
            <Input
              className="flex-1"
              value={queryKeyword}
              onChange={(_, data) => setQueryKeyword(data.value)}
              placeholder="e.g., water filter, hvac, flooring"
              onKeyPress={(e) => e.key === 'Enter' && addQueryKeyword()}
            />
            <Button
              icon={<Add24Regular />}
              onClick={addQueryKeyword}
              disabled={!queryKeyword}
            >
              Add
            </Button>
          </div>
          {conditions.query_contains?.length > 0 && (
            <TagGroup className="mt-2">
              {conditions.query_contains.map((keyword: string) => (
                <Tag
                  key={keyword}
                  dismissible
                  dismissIcon={<Delete24Regular />}
                  onClick={() => removeQueryKeyword(keyword)}
                >
                  {keyword}
                </Tag>
              ))}
            </TagGroup>
          )}
        </Field>
      </div>

      {/* Actions Section */}
      <div className="space-y-4 pt-4 border-t">
        <Text size={600} weight="semibold">Then (Actions)</Text>
        
        <Field label="Action Type" required>
          <Select
            value={actions.action_type}
            onChange={(_, data) => onActionsChange({ ...actions, action_type: data.value })}
          >
            <option value="boost">Boost Products</option>
            <option value="pin">Pin Products to Position</option>
            <option value="bury">Bury Products</option>
          </Select>
        </Field>

        {actions.action_type === 'boost' && (
          <Field label="Boost Factor" hint="Multiply relevance score by this factor">
            <Input
              type="number"
              step="0.1"
              value={actions.boost_factor?.toString() || '2.0'}
              onChange={(_, data) => onActionsChange({
                ...actions,
                boost_factor: parseFloat(data.value) || 2.0
              })}
            />
          </Field>
        )}

        {actions.action_type === 'pin' && (
          <Field label="Pin to Position" hint="Product appears at this position in results">
            <Input
              type="number"
              value={actions.pin_position?.toString() || '1'}
              onChange={(_, data) => onActionsChange({
                ...actions,
                pin_position: parseInt(data.value) || 1
              })}
            />
          </Field>
        )}

        <Field label="Products" required>
          <Button
            appearance="secondary"
            icon={<Add24Regular />}
            onClick={() => setShowProductPicker(true)}
          >
            Select Products
          </Button>
          {actions.products?.length > 0 && (
            <div className="mt-2 space-y-2">
              <Text size={300} className="text-gray-600">
                {actions.products.length} product(s) selected
              </Text>
              <TagGroup>
                {actions.products.map((productId: string) => (
                  <Tag
                    key={productId}
                    dismissible
                    dismissIcon={<Delete24Regular />}
                    onClick={() => removeProduct(productId)}
                  >
                    {productId}
                  </Tag>
                ))}
              </TagGroup>
            </div>
          )}
        </Field>
      </div>

      {showProductPicker && (
        <ProductPicker
          selectedProducts={actions.products || []}
          onSelect={handleProductsSelected}
          onClose={() => setShowProductPicker(false)}
        />
      )}
    </div>
  );
}
