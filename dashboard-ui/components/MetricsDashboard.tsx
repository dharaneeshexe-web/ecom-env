"use client";

import { motion } from "framer-motion";

const MetricsDashboard = () => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 50 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, staggerChildren: 0.2 }}
      className="grid grid-cols-2 gap-4"
    >
      <motion.div
        whileHover={{ scale: 1.05, boxShadow: "0 0 15px rgba(99, 102, 241, 0.8)" }}
        className="bg-opacity-50 bg-black rounded-2xl p-6 shadow-glow border border-purple-500"
      >
        <h3 className="text-xl font-semibold text-purple-400">Profit</h3>
        <p className="text-lg">₹10,000</p>
      </motion.div>
      <motion.div
        whileHover={{ scale: 1.05, boxShadow: "0 0 15px rgba(99, 102, 241, 0.8)" }}
        className="bg-opacity-50 bg-black rounded-2xl p-6 shadow-glow border border-purple-500"
      >
        <h3 className="text-xl font-semibold text-red-400">Fraud Loss</h3>
        <p className="text-lg">₹500</p>
      </motion.div>
      <motion.div
        whileHover={{ scale: 1.05, boxShadow: "0 0 15px rgba(99, 102, 241, 0.8)" }}
        className="bg-opacity-50 bg-black rounded-2xl p-6 shadow-glow border border-purple-500"
      >
        <h3 className="text-xl font-semibold text-green-400">Accuracy</h3>
        <p className="text-lg">95%</p>
      </motion.div>
      <motion.div
        whileHover={{ scale: 1.05, boxShadow: "0 0 15px rgba(99, 102, 241, 0.8)" }}
        className="bg-opacity-50 bg-black rounded-2xl p-6 shadow-glow border border-purple-500"
      >
        <h3 className="text-xl font-semibold text-yellow-400">Steps</h3>
        <p className="text-lg">50</p>
      </motion.div>
    </motion.div>
  );
};

export default MetricsDashboard;