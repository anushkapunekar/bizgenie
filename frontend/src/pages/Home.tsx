import { Link } from 'react-router-dom';
import { Sparkles, MessageSquare, FileText, Calendar, Zap } from 'lucide-react';

export default function Home() {
  return (
    <div className="space-y-16">
      {/* Hero Section */}
      <div className="text-center space-y-6">
        <div className="flex justify-center">
          <div className="bg-primary-100 p-4 rounded-2xl">
            <Sparkles className="h-16 w-16 text-primary-600" />
          </div>
        </div>
        <h1 className="text-5xl font-bold text-gray-900">
          Welcome to <span className="text-primary-600">BizGenie</span>
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          Your AI-powered business assistant. Handle customer queries, manage documents,
          and schedule appointments with ease.
        </p>
        <div className="flex justify-center space-x-4 pt-4">
          <Link to="/register" className="btn btn-primary text-lg px-8 py-3">
            Get Started
          </Link>
          <a
            href="https://github.com"
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-secondary text-lg px-8 py-3"
          >
            Learn More
          </a>
        </div>
      </div>

      {/* Features Grid */}
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="card text-center space-y-4">
          <div className="flex justify-center">
            <div className="bg-primary-100 p-3 rounded-lg">
              <MessageSquare className="h-8 w-8 text-primary-600" />
            </div>
          </div>
          <h3 className="text-xl font-semibold">AI Chat Agent</h3>
          <p className="text-gray-600">
            Intelligent conversation handling with LangGraph-powered routing
          </p>
        </div>

        <div className="card text-center space-y-4">
          <div className="flex justify-center">
            <div className="bg-primary-100 p-3 rounded-lg">
              <FileText className="h-8 w-8 text-primary-600" />
            </div>
          </div>
          <h3 className="text-xl font-semibold">Document Q&A</h3>
          <p className="text-gray-600">
            RAG-powered document search and question answering
          </p>
        </div>

        <div className="card text-center space-y-4">
          <div className="flex justify-center">
            <div className="bg-primary-100 p-3 rounded-lg">
              <Calendar className="h-8 w-8 text-primary-600" />
            </div>
          </div>
          <h3 className="text-xl font-semibold">Appointments</h3>
          <p className="text-gray-600">
            Smart scheduling with availability checking
          </p>
        </div>

        <div className="card text-center space-y-4">
          <div className="flex justify-center">
            <div className="bg-primary-100 p-3 rounded-lg">
              <Zap className="h-8 w-8 text-primary-600" />
            </div>
          </div>
          <h3 className="text-xl font-semibold">MCP Tools</h3>
          <p className="text-gray-600">
            Email, WhatsApp, and Calendar integrations
          </p>
        </div>
      </div>

      {/* How It Works */}
      <div className="card space-y-6">
        <h2 className="text-3xl font-bold text-center">How It Works</h2>
        <div className="grid md:grid-cols-3 gap-6">
          <div className="space-y-3">
            <div className="flex items-center space-x-3">
              <div className="bg-primary-600 text-white rounded-full w-8 h-8 flex items-center justify-center font-bold">
                1
              </div>
              <h3 className="text-lg font-semibold">Register Your Business</h3>
            </div>
            <p className="text-gray-600 ml-11">
              Create your business profile with services, working hours, and contact information.
            </p>
          </div>

          <div className="space-y-3">
            <div className="flex items-center space-x-3">
              <div className="bg-primary-600 text-white rounded-full w-8 h-8 flex items-center justify-center font-bold">
                2
              </div>
              <h3 className="text-lg font-semibold">Upload Documents</h3>
            </div>
            <p className="text-gray-600 ml-11">
              Add your business documents (PDFs) to enable AI-powered Q&A capabilities.
            </p>
          </div>

          <div className="space-y-3">
            <div className="flex items-center space-x-3">
              <div className="bg-primary-600 text-white rounded-full w-8 h-8 flex items-center justify-center font-bold">
                3
              </div>
              <h3 className="text-lg font-semibold">Start Chatting</h3>
            </div>
            <p className="text-gray-600 ml-11">
              Let your AI assistant handle customer queries, schedule appointments, and more.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

