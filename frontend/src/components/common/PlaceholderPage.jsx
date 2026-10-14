export default function PlaceholderPage({ title, description }) {
  return (
    <div className="p-8 max-w-7xl mx-auto h-full">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-slate-900">{title}</h2>
        <p className="text-slate-500 mt-1">{description}</p>
      </div>
      
      <div className="bg-white border border-slate-200 border-dashed rounded-lg p-12 flex flex-col items-center justify-center text-center">
        <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mb-4">
          <span className="text-2xl">🚧</span>
        </div>
        <h3 className="text-lg font-semibold text-slate-700">Module Under Construction</h3>
        <p className="text-slate-500 max-w-md mt-2">
          This analytical module is scheduled for implementation in a future update. 
          Please refer to the Dashboard for current insights.
        </p>
      </div>
    </div>
  );
}
