import { Link } from 'react-router-dom';
import {
  PencilSquareIcon,
  UsersIcon,
  DocumentTextIcon,
} from '@heroicons/react/24/outline';

export default function DashboardPage() {

  const quickActions = [
    {
      title: 'Find Representatives',
      description: 'Look up your state and federal representatives',
      icon: UsersIcon,
      link: '/representatives',
      color: 'bg-blue-500 hover:bg-blue-600',
    },
    {
      title: 'Writing Profiles',
      description: 'Manage your writing writing profiles',
      icon: PencilSquareIcon,
      link: '/writing-profiles',
      color: 'bg-purple-500 hover:bg-purple-600',
    },
    {
      title: 'My Letters',
      description: 'View and manage all your letters',
      icon: DocumentTextIcon,
      link: '/letters',
      color: 'bg-orange-500 hover:bg-orange-600',
    },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Welcome to Ruth</h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Your civic empowerment platform for writing to representatives
        </p>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {quickActions.map((action) => (
          <Link
            key={action.title}
            to={action.link}
            className={`${action.color} text-white rounded-lg p-6 shadow-md transition-all hover:shadow-lg`}
          >
            <action.icon className="h-8 w-8 mb-3" />
            <h3 className="text-lg font-semibold mb-1">{action.title}</h3>
            <p className="text-sm opacity-90">{action.description}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
