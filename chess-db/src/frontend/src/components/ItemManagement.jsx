import React, { useState, useEffect, useCallback } from 'react';
import { PlusCircle, Trash2, Edit2, Save, X } from 'lucide-react';

export default function ItemManagement() {
  const [items, setItems] = useState([]);
  const [newItem, setNewItem] = useState({ name: '', description: '' });
  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({ name: '', description: '' });

  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';


  const fetchItems = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/items`);
      const data = await response.json();
      setItems(data);
    } catch (error) {
      console.error('Error fetching items:', error);
    }
  }, [API_URL]);

  useEffect(() => {
    fetchItems();
  }, [fetchItems]);

  const createItem = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${API_URL}/items`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newItem)
      });
      if (response.ok) {
        setNewItem({ name: '', description: '' });
        fetchItems();
      }
    } catch (error) {
      console.error('Error creating item:', error);
    }
  };

  const updateItem = async (id) => {
    try {
      const response = await fetch(`${API_URL}/items/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(editForm)
      });
      if (response.ok) {
        setEditingId(null);
        fetchItems();
      }
    } catch (error) {
      console.error('Error updating item:', error);
    }
  };

  const deleteItem = async (id) => {
    try {
      const response = await fetch(`${API_URL}/items/${id}`, {
        method: 'DELETE'
      });
      if (response.ok) {
        fetchItems();
      }
    } catch (error) {
      console.error('Error deleting item:', error);
    }
  };

  const startEditing = (item) => {
    setEditingId(item.id);
    setEditForm({ name: item.name, description: item.description });
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Item Management</h1>
      
      {/* Create Form */}
      <form onSubmit={createItem} className="mb-8 bg-white p-4 rounded-lg shadow">
        <h2 className="text-xl font-semibold mb-4">Add New Item</h2>
        <div className="flex gap-4">
          <input
            type="text"
            placeholder="Item Name"
            value={newItem.name}
            onChange={(e) => setNewItem({ ...newItem, name: e.target.value })}
            className="flex-1 p-2 border rounded"
          />
          <input
            type="text"
            placeholder="Description"
            value={newItem.description}
            onChange={(e) => setNewItem({ ...newItem, description: e.target.value })}
            className="flex-1 p-2 border rounded"
          />
          <button
            type="submit"
            className="bg-blue-500 text-white px-4 py-2 rounded flex items-center gap-2 hover:bg-blue-600"
          >
            <PlusCircle size={20} />
            Add Item
          </button>
        </div>
      </form>

      {/* Items List */}
      <div className="bg-white rounded-lg shadow">
        <div className="grid grid-cols-1 gap-4 p-4">
          {items.map(item => (
            <div key={item.id} className="border rounded p-4">
              {editingId === item.id ? (
                <div className="flex gap-4">
                  <input
                    type="text"
                    value={editForm.name}
                    onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                    className="flex-1 p-2 border rounded"
                  />
                  <input
                    type="text"
                    value={editForm.description}
                    onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                    className="flex-1 p-2 border rounded"
                  />
                  <button
                    onClick={() => updateItem(item.id)}
                    className="bg-green-500 text-white px-4 py-2 rounded flex items-center gap-2 hover:bg-green-600"
                  >
                    <Save size={20} />
                    Save
                  </button>
                  <button
                    onClick={() => setEditingId(null)}
                    className="bg-gray-500 text-white px-4 py-2 rounded flex items-center gap-2 hover:bg-gray-600"
                  >
                    <X size={20} />
                    Cancel
                  </button>
                </div>
              ) : (
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold">{item.name}</h3>
                    <p className="text-gray-600">{item.description}</p>
                    <p className="text-sm text-gray-500">Created: {new Date(item.created_at).toLocaleString()}</p>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => startEditing(item)}
                      className="bg-yellow-500 text-white px-4 py-2 rounded flex items-center gap-2 hover:bg-yellow-600"
                    >
                      <Edit2 size={20} />
                      Edit
                    </button>
                    <button
                      onClick={() => deleteItem(item.id)}
                      className="bg-red-500 text-white px-4 py-2 rounded flex items-center gap-2 hover:bg-red-600"
                    >
                      <Trash2 size={20} />
                      Delete
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}