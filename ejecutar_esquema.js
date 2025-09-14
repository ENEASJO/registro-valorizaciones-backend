const { Client } = require('pg');
const fs = require('fs');
const path = require('path');

// Configuración de la conexión a Neon
const connectionString = process.env.NEON_DATABASE_URL || 'postgres://npg_puYoPelF96Hd:AKxHYMZXc9GyyKrf@ep-delicate-sound-167832.us-east-2.aws.neon.tech/neondb?sslmode=require';
console.log('🔗 Connection string:', connectionString.replace(/:[^:]*@/, ':***@')); // Ocultar contraseña

const client = new Client({
  connectionString: connectionString,
  ssl: {
    rejectUnauthorized: true
  }
});

async function ejecutarEsquema() {
  try {
    console.log('🔌 Conectando a Neon PostgreSQL...');
    await client.connect();
    console.log('✅ Conexión exitosa');

    // Leer el esquema SQL
    const schemaPath = path.join(__dirname, 'backend', 'sql', 'empresas_schema.sql');
    const schemaSQL = fs.readFileSync(schemaPath, 'utf8');

    console.log('📄 Ejutando esquema SQL...');
    
    // Separar las instrucciones SQL por punto y coma
    const statements = schemaSQL
      .split(';')
      .map(s => s.trim())
      .filter(s => s.length > 0 && !s.startsWith('--'));

    // Ejecutar cada instrucción
    for (let i = 0; i < statements.length; i++) {
      const statement = statements[i] + ';';
      try {
        await client.query(statement);
        console.log(`✅ Instrucción ${i + 1}/${statements.length} ejecutada`);
      } catch (error) {
        console.warn(`⚠️  Error en instrucción ${i + 1}:`, error.message);
      }
    }

    // Verificar tablas creadas
    console.log('📋 Verificando tablas creadas...');
    const result = await client.query(`
      SELECT table_name 
      FROM information_schema.tables 
      WHERE table_schema = 'public' 
      AND table_name LIKE '%empresa%'
      ORDER BY table_name
    `);

    console.log('📊 Tablas creadas:');
    result.rows.forEach(row => {
      console.log(`   - ${row.table_name}`);
    });

    console.log('🎉 ¡Esquema ejecutado exitosamente!');

  } catch (error) {
    console.error('❌ Error:', error.message);
  } finally {
    await client.end();
    console.log('🔌 Conexión cerrada');
  }
}

// Ejecutar el script
ejecutarEsquema();