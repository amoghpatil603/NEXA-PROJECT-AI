import React, { useState } from 'react';

export const ToolActivity = () => {
    const [activities, setActivities] = useState([
        { id: 1, name: 'read_file', status: 'success', time: '120ms', output: 'File content...' },
        { id: 2, name: 'execute_python', status: 'pending_approval', time: '0ms', output: '' }
    ]);

    return (
        <div className="tool-activity-panel p-4 bg-gray-50 rounded-lg">
            <h2 className="text-lg font-bold mb-4">Tool Activity</h2>
            <div className="space-y-2">
                {activities.map(activity => (
                    <div key={activity.id} className="p-2 border rounded bg-white">
                        <div className="flex justify-between">
                            <span className="font-semibold">{activity.name}</span>
                            <span className={`px-2 py-1 text-sm rounded ${activity.status === 'success' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}`}>
                                {activity.status}
                            </span>
                        </div>
                        <div className="text-sm text-gray-500 mt-1">Time: {activity.time}</div>
                        {activity.output && (
                            <pre className="mt-2 text-xs bg-gray-100 p-2 rounded overflow-x-auto">
                                {activity.output}
                            </pre>
                        )}
                        {activity.status === 'pending_approval' && (
                            <div className="mt-2 space-x-2">
                                <button className="px-3 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600">Approve</button>
                                <button className="px-3 py-1 bg-red-500 text-white rounded text-sm hover:bg-red-600">Cancel</button>
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
};
